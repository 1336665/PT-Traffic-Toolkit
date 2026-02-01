import re
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RssFeed, RssRecord, Downloader
from app.config import settings
from app.services.downloader.context import downloader_client
from app.utils import parse_size, get_logger

logger = get_logger('pt_manager.rss')


class RssService:
    """RSS feed service for fetching and filtering torrents"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_base_url(self, link: str, feed_url: str) -> str:
        """Resolve base URL from entry link or feed URL."""
        parsed = urlparse(link or "")
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        parsed = urlparse(feed_url or "")
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return ""

    def _merge_passkey_params(self, download_link: str, feed_url: str) -> str:
        """Append passkey-style params from feed URL if missing."""
        if not download_link or not feed_url:
            return download_link

        passkey_params = {"passkey", "authkey", "torrent_pass"}
        feed_params = parse_qs(urlparse(feed_url).query)
        extra = {k: v[0] for k, v in feed_params.items() if k in passkey_params and v}
        if not extra:
            return download_link

        parsed_link = urlparse(download_link)
        link_params = parse_qs(parsed_link.query)
        updated = False
        for key, value in extra.items():
            if key not in link_params:
                link_params[key] = [value]
                updated = True

        if not updated:
            return download_link

        new_query = urlencode({k: v[0] for k, v in link_params.items()})
        return urlunparse(parsed_link._replace(query=new_query))

    def _normalize_download_link(self, download_link: str, feed: RssFeed) -> str:
        """Normalize download link for common PT patterns."""
        if not download_link:
            return download_link

        if download_link.startswith('magnet:'):
            return download_link

        base_url = self._get_base_url(download_link, feed.url or "")
        parsed_link = urlparse(download_link)

        # Handle relative URLs
        if not parsed_link.scheme and base_url:
            download_link = urljoin(base_url, download_link)
            parsed_link = urlparse(download_link)

        # If link is a detail page, convert to download.php?id=xxx
        query = parse_qs(parsed_link.query)
        torrent_id = (query.get('torrentid') or query.get('id') or [""])[0]
        if torrent_id and (
            parsed_link.path.endswith('details.php')
            or parsed_link.path.endswith('torrents.php')
            or 'detail' in parsed_link.path
        ):
            download_link = urljoin(base_url, f"/download.php?id={torrent_id}")

        # Append passkey/authkey if provided in feed URL
        download_link = self._merge_passkey_params(download_link, feed.url or "")
        return download_link

    def _parse_cookie(self, cookie_str: str) -> dict:
        if not cookie_str:
            return {}
        cookies = {}
        for part in cookie_str.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key:
                    cookies[key] = value
        return cookies

    async def fetch_feed(self, feed: RssFeed, http_client: Optional[httpx.AsyncClient] = None) -> List[dict]:
        """Fetch and parse RSS feed"""
        logger.info(f"Fetching RSS feed '{feed.name}' from {feed.url[:80]}...")

        # Simple headers like a normal RSS reader - not too browser-like
        headers = {
            "User-Agent": settings.HTTP_USER_AGENT,
            "Accept": "*/*",
        }

        # Only add cookies if explicitly provided
        cookies = {}
        if feed.site_cookie:
            cookies = self._parse_cookie(feed.site_cookie)
            logger.info(f"Using {len(cookies)} cookies for feed '{feed.name}'")

        client = http_client
        close_client = False
        if client is None:
            client = httpx.AsyncClient(
                timeout=settings.HTTP_TIMEOUT,
                follow_redirects=True,
                verify=settings.HTTP_VERIFY_SSL,
            )
            close_client = True

        try:
            response = await client.get(feed.url, headers=headers, cookies=cookies if cookies else None)
            response.raise_for_status()

            content = response.text
            logger.info(f"RSS response received: {len(content)} bytes, status: {response.status_code}")

            # Log first 500 chars for debugging
            if len(content) > 0:
                logger.debug(f"RSS content preview: {content[:500]}...")

            parsed = feedparser.parse(content)

            if parsed.bozo and parsed.bozo_exception:
                logger.warning(f"RSS parse warning for '{feed.name}': {parsed.bozo_exception}")

            entries = parsed.entries
            logger.info(f"RSS feed '{feed.name}' parsed: {len(entries)} entries found")

            # Log first entry for debugging
            if entries:
                first_entry = entries[0]
                logger.debug(f"First entry keys: {list(first_entry.keys())}")
                logger.debug(f"First entry title: {first_entry.get('title', 'N/A')}")
                logger.debug(f"First entry link: {first_entry.get('link', 'N/A')}")
                if 'enclosures' in first_entry:
                    logger.debug(f"First entry enclosures: {first_entry.get('enclosures', [])}")

            return entries
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text[:500] if e.response.text else ""
            if status_code == 403:
                logger.error(f"HTTP 403 Forbidden for RSS feed '{feed.name}'")
                logger.error("可能原因: 1) passkey 无效或过期 2) 站点 IP 限制 3) CloudFlare 保护")
                logger.error("请检查 RSS 链接是否正确，尝试在浏览器中打开链接测试")
                if "cloudflare" in response_text.lower() or "cf-ray" in str(e.response.headers).lower():
                    logger.error("检测到 CloudFlare 保护，此站点可能需要特殊处理")
            elif status_code == 401:
                logger.error(f"HTTP 401 Unauthorized for RSS feed '{feed.name}' - 认证失败")
            else:
                logger.error(f"HTTP error {status_code} fetching RSS feed '{feed.name}'")
            logger.debug(f"Response preview: {response_text[:200]}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching RSS feed '{feed.name}': {type(e).__name__}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching RSS feed '{feed.name}': {type(e).__name__}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []
        finally:
            if close_client and client:
                try:
                    await client.aclose()
                except Exception:
                    pass
    def extract_torrent_info(self, entry: dict, feed: RssFeed) -> dict:
        """Extract torrent information from RSS entry with support for various PT site formats"""
        title = entry.get('title', '')
        link = entry.get('link', '') or entry.get('id', '') or entry.get('guid', '')
        description = entry.get('description', '') or entry.get('summary', '')

        logger.debug(f"Extracting info for: {title[:50]}...")

        # Try multiple sources for torrent download link
        # Priority: enclosure > links > link
        download_link = link

        # Check enclosures (common for PT RSS feeds)
        enclosures = entry.get('enclosures', [])
        if enclosures:
            for enc in enclosures:
                enc_url = enc.get('href') or enc.get('url', '')
                if enc_url:
                    download_link = enc_url
                    logger.debug(f"Found enclosure link: {enc_url[:80]}...")
                    break

        # Check links array (some feeds use this)
        links = entry.get('links', [])
        if links:
            for lnk in links:
                lnk_type = lnk.get('type', '')
                lnk_href = lnk.get('href', '')
                # Prefer torrent/magnet links
                if 'torrent' in lnk_type.lower() or lnk_href.endswith('.torrent') or lnk_href.startswith('magnet:'):
                    download_link = lnk_href
                    logger.debug(f"Found torrent link in links: {lnk_href[:80]}...")
                    break
                # Also check for download link with rel=enclosure
                if lnk.get('rel') == 'enclosure':
                    download_link = lnk_href
                    logger.debug(f"Found enclosure rel link: {lnk_href[:80]}...")
                    break

        # Normalize download link (relative URLs, passkey params, detail -> download)
        if download_link:
            download_link = self._normalize_download_link(download_link, feed)
            logger.debug(f"Normalized download link: {download_link[:80]}...")

        # Extract size from various possible fields
        size = 0

        # Try different size field names (including namespaced ones)
        size_fields = [
            'contentlength', 'torrent_contentlength',
            'size', 'torrent_size',
            'length', 'torrent_length',
        ]

        for field in size_fields:
            if field in entry:
                try:
                    val = entry[field]
                    if isinstance(val, (int, float)):
                        size = int(val)
                    else:
                        size = parse_size(str(val))
                    if size > 0:
                        logger.debug(f"Found size from {field}: {size}")
                        break
                except (ValueError, TypeError):
                    pass

        # Try from enclosure length
        if size == 0 and enclosures:
            for enc in enclosures:
                if 'length' in enc:
                    try:
                        size = int(enc['length'])
                        if size > 0:
                            logger.debug(f"Found size from enclosure length: {size}")
                            break
                    except (ValueError, TypeError):
                        pass

        # Try parsing size from title or description
        if size == 0:
            description = entry.get('description', '') or entry.get('summary', '') or ''
            # Pattern like "10.5 GB" or "500 MB"
            size_pattern = r'(\d+(?:\.\d+)?)\s*(TB|GB|MB|KB|B)\b'
            for text in [title, description]:
                match = re.search(size_pattern, text, re.IGNORECASE)
                if match:
                    num = float(match.group(1))
                    unit = match.group(2).upper()
                    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                    size = int(num * multipliers.get(unit, 1))
                    logger.debug(f"Parsed size from text: {size}")
                    break

        # Extract seeders/leechers from various possible fields
        seeders = 0
        leechers = 0

        seeder_fields = ['seeders', 'seeds', 'se', 'torrent_seeds', 'torrent_seeders']
        for key in seeder_fields:
            if key in entry:
                try:
                    seeders = int(entry[key])
                    logger.debug(f"Found seeders from {key}: {seeders}")
                    break
                except (ValueError, TypeError):
                    pass

        leecher_fields = ['leechers', 'peers', 'le', 'torrent_peers', 'torrent_leechers']
        for key in leecher_fields:
            if key in entry:
                try:
                    leechers = int(entry[key])
                    logger.debug(f"Found leechers from {key}: {leechers}")
                    break
                except (ValueError, TypeError):
                    pass

        torrent_meta = entry.get('torrent')
        if isinstance(torrent_meta, dict):
            if seeders == 0 and 'seeds' in torrent_meta:
                try:
                    seeders = int(torrent_meta['seeds'])
                    logger.debug(f"Found seeders from torrent meta: {seeders}")
                except (ValueError, TypeError):
                    pass
            if leechers == 0 and 'peers' in torrent_meta:
                try:
                    leechers = int(torrent_meta['peers'])
                    logger.debug(f"Found leechers from torrent meta: {leechers}")
                except (ValueError, TypeError):
                    pass

        # Fallback: parse seeders/leechers from description text
        if seeders == 0 or leechers == 0:
            description = entry.get('description', '') or entry.get('summary', '') or ''
            if description:
                seed_match = re.search(r'(?:seeds?|seeders?|做种|做種)[:：]?\s*(\d+)', description, re.IGNORECASE)
                leech_match = re.search(r'(?:leechers?|peers?|下载|吸血)[:：]?\s*(\d+)', description, re.IGNORECASE)
                if seeders == 0 and seed_match:
                    seeders = int(seed_match.group(1))
                    logger.debug(f"Parsed seeders from description: {seeders}")
                if leechers == 0 and leech_match:
                    leechers = int(leech_match.group(1))
                    logger.debug(f"Parsed leechers from description: {leechers}")

        # Check for HR (Hit and Run) in title/description
        is_hr = False
        hr_keywords = ['H&R', 'HR', 'hitrun', 'hit&run', 'hit and run', '[HR]', '(HR)']
        description = entry.get('description', '') or entry.get('summary', '') or ''
        for kw in hr_keywords:
            if kw.lower() in title.lower() or kw.lower() in description.lower():
                is_hr = True
                logger.debug(f"Found HR marker: {kw}")
                break

        # Check for Free status in title/description
        is_free = False
        free_keywords = ['free', '免费', '[免费]', '(免费)', 'freeleech', '[free]', '2xfree', '2x free']
        for kw in free_keywords:
            if kw.lower() in title.lower() or kw.lower() in description.lower():
                is_free = True
                logger.debug(f"Found Free marker: {kw}")
                break

        categories = []
        if entry.get('category'):
            categories.append(str(entry.get('category')))
        for tag in entry.get('tags', []) or []:
            term = tag.get('term') if isinstance(tag, dict) else str(tag)
            if term:
                categories.append(str(term))

        info = {
            'title': title,
            'link': download_link,
            'description': description,
            'size': size,
            'seeders': seeders,
            'leechers': leechers,
            'is_hr': is_hr,
            'is_free': is_free,
            'torrent_hash': '',
            'categories': [c.strip() for c in categories if str(c).strip()],
        }

        logger.debug(f"Extracted info: title='{title[:30]}...', link='{download_link[:50]}...', size={size}, seeders={seeders}")
        return info

    async def check_free_status(
        self,
        torrent_url: str,
        feed: RssFeed,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[bool, str]:
        """Check if torrent is free by visiting the detail page"""
        if not feed.site_cookie:
            return False, ""

        # Extract detail page URL from torrent URL if needed
        detail_url = torrent_url

        # If it's a direct .torrent URL, try to extract detail page
        if torrent_url.endswith('.torrent') or 'download' in torrent_url.lower():
            # Try to find torrent ID and construct detail URL
            id_match = re.search(r'[?&]id=(\d+)', torrent_url)
            if id_match and feed.url:
                parsed = urlparse(feed.url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                detail_url = f"{base_url}/details.php?id={id_match.group(1)}"
            else:
                return False, ""

        headers = {
            "Cookie": feed.site_cookie,
            "User-Agent": settings.HTTP_USER_AGENT,
        }

        client = http_client
        close_client = False
        if client is None:
            client = httpx.AsyncClient(
                timeout=settings.HTTP_TIMEOUT,
                follow_redirects=True,
                verify=settings.HTTP_VERIFY_SSL,
            )
            close_client = True

        try:
            response = await client.get(detail_url, headers=headers)
            response.raise_for_status()

            page_text = response.text.lower()

            # Common free indicators
            free_indicators = [
                'class="free"', 'class="pro_free"',
                'pro_free', 'freeleech',
                '免费', '免費',
                'promotion-free', 'free_icon',
                'torrent-icons free', '"free"',
                '2x free', '2xfree',
            ]

            is_free = any(ind.lower() in page_text for ind in free_indicators)

            # Try to extract torrent hash from page
            torrent_hash = ""
            hash_match = re.search(r'[a-fA-F0-9]{40}', response.text)
            if hash_match:
                torrent_hash = hash_match.group(0).lower()

            return is_free, torrent_hash
        except Exception as e:
            logger.debug(f"Error checking free status for {detail_url}: {e}")
            return False, ""
        finally:
            if close_client and client:
                try:
                    await client.aclose()
                except Exception:
                    pass
    def filter_torrent(self, info: dict, feed: RssFeed) -> Tuple[bool, str]:
        """Check if torrent passes all filters, return (pass, skip_reason)"""
        # Size filter (only if size is known and filter is set)
        size_gb = info['size'] / (1024 ** 3) if info['size'] > 0 else 0

        if feed.min_size > 0 and info['size'] > 0 and size_gb < feed.min_size:
            return False, f"Size too small: {size_gb:.2f}GB < {feed.min_size}GB"
        if feed.max_size > 0 and info['size'] > 0 and size_gb > feed.max_size:
            return False, f"Size too large: {size_gb:.2f}GB > {feed.max_size}GB"

        # Seeders filter (only if seeders info is available and filter is set)
        if feed.min_seeders > 0 and info['seeders'] > 0 and info['seeders'] < feed.min_seeders:
            return False, f"Too few seeders: {info['seeders']} < {feed.min_seeders}"
        if feed.max_seeders > 0 and info['seeders'] > 0 and info['seeders'] > feed.max_seeders:
            return False, f"Too many seeders: {info['seeders']} > {feed.max_seeders}"

        # HR filter
        if feed.exclude_hr and info['is_hr']:
            return False, "HR torrent excluded"

        # Free filter
        if feed.only_free and not info['is_free']:
            return False, "Not free"

        # Keyword filters
        title = info['title'].lower()

        if feed.include_keywords:
            include_list = [k.strip().lower() for k in feed.include_keywords.split(',') if k.strip()]
            if include_list and not any(kw in title for kw in include_list):
                return False, f"No matching include keywords: {feed.include_keywords}"

        if feed.exclude_keywords:
            exclude_list = [k.strip().lower() for k in feed.exclude_keywords.split(',') if k.strip()]
            for kw in exclude_list:
                if kw in title:
                    return False, f"Matched exclude keyword: {kw}"

        return True, ""

    async def get_best_downloader(self) -> Optional[Downloader]:
        """Get downloader with most free space"""
        result = await self.db.execute(
            select(Downloader).where(Downloader.enabled == True)
        )
        downloaders = result.scalars().all()

        if not downloaders:
            logger.warning("No enabled downloaders found")
            return None

        best_downloader = None
        best_free_space = 0

        for dl in downloaders:
            try:
                async with downloader_client(dl) as client:
                    if not client:
                        continue
                    free_space = await client.get_free_space()
                    logger.debug(f"Downloader '{dl.name}' free space: {free_space / (1024**3):.2f} GB")

                    if free_space > best_free_space:
                        best_free_space = free_space
                        best_downloader = dl
            except Exception as e:
                logger.debug(f"Error checking downloader '{dl.name}': {e}")
                continue

        if best_downloader:
            logger.info(
                f"Selected downloader: {best_downloader.name} with {best_free_space / (1024**3):.2f} GB free"
            )

        return best_downloader
    async def download_torrent_file(
        self,
        url: str,
        cookie: str = "",
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[bytes]:
        """Download .torrent file from URL"""
        if not url or url.startswith('magnet:'):
            return None

        headers = {
            "User-Agent": settings.HTTP_USER_AGENT,
        }
        if cookie:
            headers["Cookie"] = cookie

        client = http_client
        close_client = False
        if client is None:
            client = httpx.AsyncClient(
                timeout=settings.HTTP_TIMEOUT,
                follow_redirects=True,
                verify=settings.HTTP_VERIFY_SSL,
            )
            close_client = True

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')

            # Check if it's a torrent file
            if (
                'application/x-bittorrent' in content_type
                or url.endswith('.torrent')
                or response.content[:11] == b'd8:announce'  # Torrent file signature
            ):
                logger.debug(f"Downloaded torrent file: {len(response.content)} bytes")
                return response.content

            # Return content anyway, might be torrent
            logger.debug(f"Downloaded content: {len(response.content)} bytes, type: {content_type}")
            return response.content
        except Exception as e:
            logger.error(f"Error downloading torrent from {url[:80]}...: {e}")
            return None
        finally:
            if close_client and client:
                try:
                    await client.aclose()
                except Exception:
                    pass
    async def process_feed(self, feed: RssFeed) -> List[RssRecord]:
        """Process RSS feed: fetch, filter, and optionally download"""
        logger.info("=" * 60)
        logger.info(f"Processing RSS feed '{feed.name}'")
        logger.info(f"URL: {feed.url[:80]}...")
        logger.info(f"First run done: {feed.first_run_done}")
        logger.info(f"Enabled: {feed.enabled}")

        records: List[RssRecord] = []

        async with httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            follow_redirects=True,
            verify=settings.HTTP_VERIFY_SSL,
        ) as http_client:
            entries = await self.fetch_feed(feed, http_client=http_client)

            if not entries:
                logger.warning(f"No entries found for RSS feed '{feed.name}'")
                feed.last_fetch = datetime.utcnow()
                await self.db.commit()
                return records

            # Extract info from entries first (dedup within this run)
            candidates: List[dict] = []
            candidate_links: List[str] = []
            seen_links: Set[str] = set()

            for entry in entries:
                info = self.extract_torrent_info(entry, feed)
                link = info.get('link')
                if not link:
                    continue
                if link in seen_links:
                    continue
                seen_links.add(link)
                candidates.append(info)
                candidate_links.append(link)

            if not candidates:
                logger.info(f"No valid links found for RSS feed '{feed.name}'")
                feed.last_fetch = datetime.utcnow()
                await self.db.commit()
                return records

            # Query existing links only for the current batch to avoid loading the whole history
            existing_links: Set[str] = set()
            chunk_size = 500  # SQLite has a variable limit; keep this conservative
            for i in range(0, len(candidate_links), chunk_size):
                chunk = candidate_links[i:i + chunk_size]
                result = await self.db.execute(
                    select(RssRecord.link).where(
                        RssRecord.feed_id == feed.id,
                        RssRecord.link.in_(chunk),
                    )
                )
                existing_links.update(row[0] for row in result.fetchall())

            entries_info = [info for info in candidates if info['link'] not in existing_links]

            new_count = len(entries_info)
            logger.info(f"RSS feed '{feed.name}': {len(entries)} total, {new_count} new entries")

            if not entries_info:
                logger.info(f"No new entries to process for feed '{feed.name}'")
                feed.last_fetch = datetime.utcnow()
                await self.db.commit()
                return records

            # Parallel free status check if only_free is enabled (bounded concurrency)
            if feed.only_free and feed.site_cookie and entries_info:
                max_conc = max(1, int(getattr(settings, 'RSS_MAX_CONCURRENT_FREE_CHECKS', 8)))
                logger.info(f"Checking free status for {len(entries_info)} entries (max_concurrency={max_conc})...")
                sem = asyncio.Semaphore(max_conc)

                async def check_free(info: dict) -> dict:
                    async with sem:
                        is_free, torrent_hash = await self.check_free_status(
                            info['link'],
                            feed,
                            http_client=http_client,
                        )
                        info['is_free'] = is_free or info['is_free']  # Keep if already marked free
                        if torrent_hash:
                            info['torrent_hash'] = torrent_hash
                        return info

                entries_info = await asyncio.gather(*[check_free(info) for info in entries_info])

            passed_count = 0
            downloaded_count = 0

            for info in entries_info:
                # Filter check
                passed, skip_reason = self.filter_torrent(info, feed)

                logger.info(
                    f"Entry: {info['title'][:50]}... | Pass: {passed} | Reason: {skip_reason or 'OK'}"
                )

                # Create record
                record = RssRecord(
                    feed_id=feed.id,
                    title=info['title'],
                    link=info['link'],
                    torrent_hash=info['torrent_hash'],
                    size=info['size'],
                    is_free=info['is_free'],
                    is_hr=info['is_hr'],
                    seeders=info['seeders'],
                    leechers=info['leechers'],
                    downloaded=False,
                    skip_reason=skip_reason if not passed else "",
                )

                if passed:
                    passed_count += 1

                # Download if passed and not first run
                if passed and feed.first_run_done:
                    downloader = None

                    if feed.auto_assign or not feed.downloader_id:
                        downloader = await self.get_best_downloader()
                    elif feed.downloader_id:
                        result = await self.db.execute(
                            select(Downloader).where(Downloader.id == feed.downloader_id)
                        )
                        downloader = result.scalar_one_or_none()

                    if downloader:
                        logger.info(f"Adding torrent '{info['title'][:50]}...' to {downloader.name}")
                        success = await self._add_to_downloader(
                            info['link'],
                            downloader,
                            feed,
                            http_client=http_client,
                        )
                        if success:
                            record.downloaded = True
                            record.download_time = datetime.utcnow()
                            record.downloader_id = downloader.id
                            downloaded_count += 1
                            logger.info(f"Successfully added torrent: {info['title'][:50]}...")
                        else:
                            logger.warning(f"Failed to add torrent: {info['title'][:50]}...")
                            record.skip_reason = "Failed to add to downloader"
                    else:
                        logger.warning(f"No downloader available for torrent: {info['title'][:50]}...")
                        record.skip_reason = "No downloader available"
                elif passed and not feed.first_run_done:
                    logger.info(
                        f"First run - recording entry without downloading: {info['title'][:50]}..."
                    )

                self.db.add(record)
                records.append(record)

        # Mark first run as done
        if not feed.first_run_done:
            feed.first_run_done = True
            logger.info(f"RSS feed '{feed.name}' first run completed, recorded {len(records)} entries")

        feed.last_fetch = datetime.utcnow()
        await self.db.commit()

        logger.info(
            f"RSS feed '{feed.name}' processed: {len(records)} new, {passed_count} passed filter, {downloaded_count} downloaded"
        )
        logger.info("=" * 60)
        return records
    async def _add_to_downloader(
        self,
        torrent_link: str,
        downloader: Downloader,
        feed: RssFeed,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> bool:
        """Add torrent to downloader"""
        try:
            async with downloader_client(downloader) as client:
                if not client:
                    logger.error(f"Failed to connect to downloader: {downloader.name}")
                    return False

                # Check downloader limits
                stats = None
                try:
                    stats = await client.get_stats()
                except Exception as e:
                    logger.warning(f"Failed to get downloader stats: {e}")

                if (
                    getattr(feed, 'max_download_tasks', 0)
                    and stats
                    and stats.downloading_torrents >= feed.max_download_tasks
                ):
                    logger.warning(
                        f"Downloader {downloader.name} at max download tasks: {stats.downloading_torrents}"
                    )
                    return False

                # Download torrent file or use magnet
                torrent_data = None
                if not torrent_link.startswith('magnet:'):
                    torrent_data = await self.download_torrent_file(
                        torrent_link,
                        feed.site_cookie,
                        http_client=http_client,
                    )
                    if not torrent_data:
                        logger.error(f"Failed to download torrent file from: {torrent_link[:80]}...")
                        return False

                upload_limit = 0
                download_limit = 0

                if getattr(feed, 'max_upload_speed', 0):
                    upload_limit = int(feed.max_upload_speed * 1024)
                if getattr(feed, 'max_download_speed', 0):
                    download_limit = int(feed.max_download_speed * 1024)

                first_last = getattr(downloader, 'download_first_last', False)

                # Get qBittorrent-specific settings from feed
                qb_category = getattr(feed, 'qb_category', '') or None
                qb_tags_str = getattr(feed, 'qb_tags', '') or ''
                qb_tags = [t.strip() for t in qb_tags_str.split(',') if t.strip()] if qb_tags_str else None
                qb_save_path = getattr(feed, 'qb_save_path', '') or None

                # Use feed's save_path if set, otherwise use downloader's default
                save_path = qb_save_path or (downloader.download_dir if downloader.download_dir else None)

                torrent_hash = await client.add_torrent(
                    torrent_data or torrent_link,
                    save_path=save_path,
                    category=qb_category,
                    tags=qb_tags,
                    upload_limit=upload_limit,
                    download_limit=download_limit,
                    first_last_priority=first_last,
                )

                if torrent_hash:
                    logger.info(f"Added torrent with hash: {torrent_hash}")
                    return True

                logger.error("Failed to add torrent - no hash returned")
                return False

        except Exception as e:
            logger.error(f"Error adding torrent to downloader: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False