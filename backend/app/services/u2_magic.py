"""
U2 Magic 追魔服务 - 完整移植版
基于 catch_magic.py

核心功能:
- 自动抓取U2魔法信息
- 智能筛选Free种子
- 搭桥功能支持
- 新旧种判断（按发布时间）
- 魔法生效延迟检测
- Peer列表检查
- 重复下载控制
"""

import gc
import json
import os
import re
import shutil
import asyncio
from datetime import datetime, timezone
from time import time
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, OrderedDict
from concurrent.futures import ThreadPoolExecutor

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import U2MagicConfig, U2MagicRecord, Downloader, SystemSettings
from app.services.downloader.context import downloader_client
from app.utils import parse_size, get_logger

logger = get_logger('pt_manager.u2_magic')


class U2MagicService:
    """U2 追魔服务 - 完整版"""

    BASE_URL = "https://u2.dmhy.org"
    MAGIC_LIST_URL = "https://u2.dmhy.org/promotion.php?action=list&page={}"
    MAGIC_DETAIL_URL = "https://u2.dmhy.org/promotion.php?action=detail&id={}"
    TORRENT_DETAIL_URL = "https://u2.dmhy.org/details.php?id={}"
    PEER_LIST_URL = "https://u2.dmhy.org/viewpeerlist.php?id={}"
    DOWNLOAD_URL = "https://u2.dmhy.org/download.php?id={}"

    # 第三方API (u2.kysdm.com)
    API_URL = "https://u2.kysdm.com/api/v1/promotion"

    # 时区前缀后缀（用于解析）
    TZ_PATTERNS = [
        ('时区', '，点击修改。'),
        ('時區', '，點擊修改。'),
        ('Current timezone is ', ', click to change.'),
    ]

    # 魔法类型映射
    MAGIC_TYPES = {
        'free': {'dr': 0.0},
        '2up': {'ur': 2.0},
        '50pct': {'dr': 0.5},
        '30pct': {'dr': 0.3},
        'custom': {},
    }

    STATE_KEY = "u2_magic_state"
    # Maximum number of torrent add times to track (prevents memory leak)
    MAX_TID_ADD_TIME_ENTRIES = 500

    def __init__(self, db: AsyncSession):
        self.db = db
        self.checked: deque = deque(maxlen=200)  # 已检查的魔法ID
        self.magic_id_0: Optional[int] = None    # 最新魔法ID
        # Use OrderedDict with size limit to prevent memory leak
        self._tid_add_time: OrderedDict[str, float] = OrderedDict()
        self.first_time = True
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def tid_add_time(self) -> OrderedDict[str, float]:
        """Get tid_add_time dict (for compatibility)"""
        return self._tid_add_time

    @tid_add_time.setter
    def tid_add_time(self, value: Dict[str, float]):
        """Set tid_add_time with size limiting"""
        self._tid_add_time = OrderedDict(value)
        self._cleanup_tid_add_time()

    def _cleanup_tid_add_time(self):
        """Remove oldest entries if exceeding max size"""
        while len(self._tid_add_time) > self.MAX_TID_ADD_TIME_ENTRIES:
            self._tid_add_time.popitem(last=False)

    def _set_tid_add_time(self, tid: str, timestamp: float):
        """Set a torrent add time with automatic cleanup"""
        self._tid_add_time[tid] = timestamp
        # Move to end (most recently used)
        self._tid_add_time.move_to_end(tid)
        self._cleanup_tid_add_time()

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """关闭HTTP客户端"""
        if self._http_client:
            await self._http_client.aclose()

    async def get_config(self) -> Optional[U2MagicConfig]:
        """获取配置"""
        result = await self.db.execute(select(U2MagicConfig).limit(1))
        return result.scalar_one_or_none()

    async def load_state(self):
        """加载状态"""
        try:
            result = await self.db.execute(
                select(SystemSettings).where(SystemSettings.key == self.STATE_KEY)
            )
            setting = result.scalar_one_or_none()
            if setting and setting.value:
                data = json.loads(setting.value)
                self.checked = deque(data.get('checked', []), maxlen=200)
                self.magic_id_0 = data.get('id_0')
                self.tid_add_time = data.get('add_time', {})
                logger.info(f"已加载U2追魔状态: {len(self.checked)} 条记录")
        except Exception as e:
            logger.error(f"加载U2追魔状态失败: {e}")

    async def save_state(self):
        """保存状态"""
        try:
            state_data = json.dumps({
                'checked': list(self.checked),
                'id_0': self.magic_id_0,
                'add_time': self.tid_add_time,
            })

            result = await self.db.execute(
                select(SystemSettings).where(SystemSettings.key == self.STATE_KEY)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = state_data
            else:
                setting = SystemSettings(key=self.STATE_KEY, value=state_data)
                self.db.add(setting)

            await self.db.commit()
        except Exception as e:
            logger.error(f"保存U2追魔状态失败: {e}")

    async def _make_request(
        self,
        url: str,
        cookie: str,
        method: str = "GET"
    ) -> Optional[str]:
        """发起HTTP请求"""
        try:
            client = await self._get_client()
            headers = {
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            if method == "GET":
                response = await client.get(url, headers=headers)
            else:
                response = await client.post(url, headers=headers)

            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"U2请求失败 [{url}]: {e}")
            return None

    def _get_soup(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html.replace('\n', ''), 'lxml')

    def _get_timezone(self, soup: BeautifulSoup) -> Optional[Any]:
        """获取用户时区"""
        try:
            import pytz
            tz_link = soup.find('a', {'href': 'usercp.php?action=tracker#timezone'})
            if not tz_link:
                return None
            tz_info = tz_link.get('title', '')
            for pre, suf in self.TZ_PATTERNS:
                if tz_info.startswith(pre):
                    tz_str = tz_info[len(pre):-len(suf)].strip()
                    return pytz.timezone(tz_str)
        except Exception as e:
            logger.debug(f"获取时区失败: {e}")
        return None

    def _parse_time_delta(self, date_str: str, tz) -> float:
        """计算时间差"""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            if tz:
                dt = tz.localize(dt)
            return time() - dt.timestamp()
        except (ValueError, TypeError, AttributeError, OSError):
            return 0

    def _get_promotion_info(self, td) -> Dict[str, float]:
        """解析流量优惠信息"""
        pro = {'ur': 1.0, 'dr': 1.0}
        try:
            for img in td.select('img') or []:
                img_class = img.get('class', [])
                if not img_class:
                    continue
                class_str = img_class[0] if isinstance(img_class, list) else img_class

                for key, data in self.MAGIC_TYPES.items():
                    if key in class_str:
                        pro.update(data)
                        break
                else:
                    # 自定义倍率
                    if 'arrowup' in class_str:
                        try:
                            text = img.next.text if img.next else ''
                            pro['ur'] = float(text[:-1].replace(',', '.'))
                        except (ValueError, TypeError, AttributeError, IndexError):
                            pass
                    elif 'arrowdown' in class_str:
                        try:
                            text = img.next.text if img.next else ''
                            pro['dr'] = float(text[:-1].replace(',', '.'))
                        except (ValueError, TypeError, AttributeError, IndexError):
                            pass
        except Exception as e:
            logger.debug(f"解析流量优惠失败: {e}")
        try:
            promo_text = td.get_text(" ", strip=True).lower()
            if re.search(r'2x', promo_text) and ('free' in promo_text or '免费' in promo_text):
                pro['ur'] = 2.0
                pro['dr'] = 0.0
            elif 'free' in promo_text or '免费' in promo_text:
                pro['dr'] = 0.0
        except Exception:
            pass
        return pro

    def _extract_size_bytes(self, soup: BeautifulSoup) -> int:
        """解析种子体积（字节）"""
        time_tag = soup.time
        if not time_tag or not time_tag.parent:
            return 0

        contents = time_tag.parent.contents
        if len(contents) <= 5:
            return 0

        size_str = contents[5].strip() if hasattr(contents[5], 'strip') else ''
        size_str = size_str.replace(',', '.').replace('Б', 'B')
        size_bytes = parse_size(size_str)

        if size_bytes == 0:
            parts = size_str.split()
            if len(parts) >= 2:
                try:
                    num = float(parts[0])
                    unit = parts[1]
                except ValueError:
                    return 0
                unit_map = {
                    'MIB': 1024 ** 2,
                    'GIB': 1024 ** 3,
                    'TIB': 1024 ** 4,
                    '喵': 1024 ** 2,
                    '寄': 1024 ** 3,
                    '烫': 1024 ** 4,
                    'EGAMAY': 1024 ** 2,
                    'IGAGAY': 1024 ** 3,
                    'ERATAY': 1024 ** 4,
                }
                size_bytes = int(num * unit_map.get(unit.upper(), 0))

        return int(size_bytes)

    def _format_magic_type(self, promo_info: Dict[str, float]) -> str:
        """根据优惠倍率生成魔法类型文本"""
        ur = promo_info.get('ur', 1.0)
        dr = promo_info.get('dr', 1.0)

        if dr == 0:
            if ur > 1:
                return f"{int(ur)}xFree" if float(ur).is_integer() else f"{ur}xFree"
            return "Free"

        if ur > 1:
            return f"{int(ur)}x" if float(ur).is_integer() else f"{ur}x"

        if dr < 1:
            return f"{int(dr * 100)}%"

        return "Normal"

    async def fetch_magic_from_api(
        self,
        config: U2MagicConfig
    ) -> List[Tuple[int, int]]:
        """通过API获取魔法列表"""
        if not config.api_token:
            return []

        try:
            client = await self._get_client()
            params = {
                'uid': config.uid if hasattr(config, 'uid') else 0,
                'token': config.api_token,
                'scope': 'public',
                'maximum': 30,
            }

            response = await client.get(self.API_URL, params=params)
            data = response.json()

            pro_list = data.get('data', {}).get('promotion', [])

            # 如果配置了私人魔法
            if config.magic_self if hasattr(config, 'magic_self') else False:
                params['scope'] = 'private'
                response = await client.get(self.API_URL, params=params)
                private_data = response.json()
                private_list = private_data.get('data', {}).get('promotion', [])
                pro_list.extend([
                    p for p in private_list
                    if p.get('for_user_id') == params['uid']
                ])

            results = []
            for pro_data in pro_list:
                magic_id = pro_data.get('promotion_id')
                tid = pro_data.get('torrent_id')

                if magic_id == self.magic_id_0:
                    break

                if magic_id not in self.checked:
                    if self.first_time and not self.magic_id_0:
                        self.checked.append(magic_id)
                    else:
                        results.append((magic_id, tid))

            if pro_list:
                self.magic_id_0 = pro_list[0].get('promotion_id')

            return results
        except Exception as e:
            logger.error(f"API获取魔法失败: {e}")
            return []

    async def fetch_magic_from_web(
        self,
        config: U2MagicConfig
    ) -> List[Tuple[int, int]]:
        """通过网页获取魔法列表"""
        all_checked = self.first_time and not self.magic_id_0
        index = 0
        id_0 = self.magic_id_0
        results = []

        while True:
            html = await self._make_request(
                self.MAGIC_LIST_URL.format(index),
                config.cookie
            )
            if not html:
                break

            soup = self._get_soup(html)

            # 获取用户ID
            info_block = soup.find('table', {'id': 'info_block'})
            if not info_block or not info_block.a:
                break
            user_id = info_block.a.get('href', '')[19:]

            # 解析魔法表格
            magic_table = soup.find('table', {'width': '99%'})
            if not magic_table:
                break

            rows = list(magic_table.children)
            for i, tr in enumerate(rows):
                if i == 0:  # 跳过表头
                    continue
                if not hasattr(tr, 'contents') or len(tr.contents) < 6:
                    continue

                try:
                    magic_id = int(tr.contents[0].string)

                    # 记录最新ID
                    if index == 0 and i == 1:
                        self.magic_id_0 = magic_id
                        if self.first_time and id_0 and magic_id - id_0 > 10 * 120:
                            all_checked = True

                    # 检查是否已失效或已处理
                    status = tr.contents[5].string if len(tr.contents) > 5 else ''
                    if status in ['Expired', '已失效'] or magic_id == id_0:
                        all_checked = True
                        break

                    # 检查是否是魔法类型
                    magic_type = tr.contents[1].string if len(tr.contents) > 1 else ''
                    if magic_type not in ['魔法', 'Magic', 'БР']:
                        if magic_id not in self.checked:
                            self.checked.append(magic_id)
                        continue

                    # 检查是否终止
                    if status in ['Terminated', '终止', '終止', 'Прекращён']:
                        if magic_id not in self.checked:
                            self.checked.append(magic_id)
                        continue

                    # 检查目标用户
                    target_cell = tr.contents[3] if len(tr.contents) > 3 else None
                    is_for_all = target_cell and target_cell.string in ['所有人', 'Everyone', 'Для всех']
                    is_for_self = (
                        target_cell and target_cell.a and
                        target_cell.a.get('href', '')[19:] == user_id and
                        (config.magic_self if hasattr(config, 'magic_self') else False)
                    )

                    if not is_for_all and not is_for_self:
                        if magic_id not in self.checked:
                            self.checked.append(magic_id)
                        continue

                    # 获取种子ID
                    torrent_cell = tr.contents[2] if len(tr.contents) > 2 else None
                    if not torrent_cell or not torrent_cell.a:
                        if magic_id not in self.checked:
                            self.checked.append(magic_id)
                        continue

                    tid = int(torrent_cell.a.get('href', '')[15:])

                    if magic_id not in self.checked:
                        if self.first_time and all_checked:
                            self.checked.append(magic_id)
                        else:
                            results.append((magic_id, tid))

                except Exception as e:
                    logger.debug(f"解析魔法行失败: {e}")
                    continue

            if all_checked:
                break
            index += 1

        return results

    async def analyze_magic(
        self,
        magic_id: int,
        tid: int,
        config: U2MagicConfig
    ) -> Optional[Dict[str, Any]]:
        """分析单个魔法，决定是否下载"""
        # 获取种子详情页
        html = await self._make_request(
            self.TORRENT_DETAIL_URL.format(tid),
            config.cookie
        )
        if not html:
            return None

        soup = self._get_soup(html)

        # 检查种子是否存在
        index_links = soup.select('a.index')
        if len(index_links) < 2:
            logger.debug(f"种子 {tid} 已删除")
            return None

        torrent_name = index_links[0].text[5:-8] if index_links[0].text else f"torrent_{tid}"
        download_link = f"{self.BASE_URL}/{index_links[1].get('href', '')}"

        # 名称过滤
        name_filter = config.name_filter.split(',') if hasattr(config, 'name_filter') and config.name_filter else []
        if name_filter:
            title = soup.find('h1', {'align': 'center', 'id': 'top'})
            title_text = title.text if title else ''
            if any(kw.strip() in title_text or kw.strip() in torrent_name for kw in name_filter if kw.strip()):
                logger.debug(f"种子 {tid} 被名称过滤")
                return None

        # 分类过滤
        cat_filter = config.categories.split(',') if config.categories else []
        if cat_filter:
            time_tag = soup.time
            if time_tag and time_tag.parent:
                contents = time_tag.parent.contents
                if len(contents) > 7:
                    cat = contents[7].strip() if hasattr(contents[7], 'strip') else str(contents[7]).strip()
                    if cat and cat not in [c.strip() for c in cat_filter]:
                        logger.debug(f"种子 {tid} 分类 {cat} 不匹配")
                        return None

        # 体积过滤
        size_bytes = self._extract_size_bytes(soup)
        if size_bytes > 0 and (config.min_size > 0 or config.max_size > 0):
            gb = size_bytes / (1024 ** 3)
            if config.min_size > 0 and gb < config.min_size:
                logger.debug(f"种子 {tid} 体积 {gb:.2f}GB 小于最小值")
                return None
            if config.max_size > 0 and gb > config.max_size:
                logger.debug(f"种子 {tid} 体积 {gb:.2f}GB 大于最大值")
                return None

        # 获取时区
        tz = self._get_timezone(soup)

        # 获取发布时间
        time_tag = soup.time
        publish_date = time_tag.get('title') or time_tag.text if time_tag else ''
        delta = self._parse_time_delta(publish_date, tz)

        # 获取做种人数
        peercount_div = soup.find('div', {'id': 'peercount'})
        seeders = 0
        if peercount_div and peercount_div.b:
            match = re.search(r'(\d+)', peercount_div.b.text)
            if match:
                seeders = int(match.group(1))

        # 判断新旧种（按发布时间）
        min_day = config.min_day if hasattr(config, 'min_day') else 7
        is_new = delta < min_day * 86400

        # 获取当前流量优惠
        promo_info = {'ur': 1.0, 'dr': 1.0}
        for tr in soup.find_all('tr'):
            if tr.td and tr.td.text in ['流量优惠', '流量優惠', 'Promotion', 'Тип раздачи (Бонусы)']:
                if len(tr.contents) > 1:
                    promo_info = self._get_promotion_info(tr.contents[1])
                break

        is_free = promo_info['dr'] == 0
        magic_type = self._format_magic_type(promo_info)

        # 新种逻辑
        if is_new:
            if not config.download_new:
                logger.debug(f"种子 {tid} 是新种，已禁用新种下载")
                return None

            if seeders > config.max_seeders:
                logger.debug(f"种子 {tid} 做种人数 {seeders} > {config.max_seeders}")
                return None

            if not is_free:
                logger.debug(f"种子 {tid} 新种不是Free")
                return None

            return {
                'magic_id': magic_id,
                'tid': tid,
                'name': torrent_name,
                'download_link': download_link,
                'seeders': seeders,
                'is_new': True,
                'is_free': is_free,
                'magic_type': magic_type,
                'size': size_bytes,
            }

        # 旧种逻辑
        if not config.download_old:
            logger.debug(f"种子 {tid} 是旧种，已禁用旧种下载")
            return None

        # 检查是否Free或即将Free
        download_non_free = config.download_non_free if hasattr(config, 'download_non_free') else False
        if not is_free and not download_non_free:
            # 检查魔法是否即将生效
            effective_delay = config.effective_delay if hasattr(config, 'effective_delay') else 60

            magic_html = await self._make_request(
                self.MAGIC_DETAIL_URL.format(magic_id),
                config.cookie
            )
            if magic_html:
                magic_soup = self._get_soup(magic_html)
                magic_table = magic_soup.find('table', {'width': '75%', 'cellpadding': '4'})
                if magic_table and magic_table.tbody:
                    rows = list(magic_table.tbody.children)
                    if len(rows) > 6:
                        magic_promo = self._get_promotion_info(rows[6].contents[1] if len(rows[6].contents) > 1 else rows[6])
                        if magic_promo['dr'] == 0:
                            # 是Free魔法，检查生效时间
                            if len(rows) > 4 and len(rows[4].contents) > 1:
                                time_cell = rows[4].contents[1]
                                time_tag = time_cell.time if hasattr(time_cell, 'time') else None
                                if time_tag:
                                    date_str = time_tag.get('title') or time_tag.text
                                    delay = -self._parse_time_delta(date_str, self._get_timezone(magic_soup))
                                    if -1 < delay < effective_delay:
                                        logger.info(f"种子 {tid} Free魔法将在 {int(delay)}秒后生效")
                                        # 继续下载
                                    else:
                                        return None
                        else:
                            return None
                else:
                    return None
            else:
                return None

        # 检查做种人数
        download_dead = config.download_dead if hasattr(config, 'download_dead') else False
        if seeders == 0 and not download_dead:
            logger.debug(f"种子 {tid} 无人做种")
            return None

        if seeders > config.max_seeders:
            # 检查搭桥
            da_qiao = config.da_qiao if hasattr(config, 'da_qiao') else True
            if da_qiao:
                magic_html = await self._make_request(
                    self.MAGIC_DETAIL_URL.format(magic_id),
                    config.cookie
                )
                if magic_html:
                    magic_soup = self._get_soup(magic_html)
                    legend = magic_soup.legend
                    if legend and legend.parent:
                        comment = legend.parent.contents[1].text if len(legend.parent.contents) > 1 else ''
                        if ('搭' in comment and '桥' in comment) or ('加' in comment and '速' in comment):
                            user_bdo = magic_soup.select('table.main bdo')
                            user_name = user_bdo[0].text if user_bdo else 'Unknown'
                            logger.info(f"种子 {tid} 用户 {user_name} 搭桥请求，下载中...")
                            return {
                                'magic_id': magic_id,
                                'tid': tid,
                                'name': torrent_name,
                                'download_link': download_link,
                                'seeders': seeders,
                                'is_new': False,
                                'is_free': is_free,
                                'is_bridge': True,
                                'magic_type': magic_type,
                                'size': size_bytes,
                            }

            logger.debug(f"种子 {tid} 做种人数 {seeders} > {config.max_seeders}")
            return None

        return {
            'magic_id': magic_id,
            'tid': tid,
            'name': torrent_name,
            'download_link': download_link,
            'seeders': seeders,
            'is_new': False,
            'is_free': is_free,
            'magic_type': magic_type,
            'size': size_bytes,
        }

    async def download_torrent(
        self,
        download_link: str,
        tid: str,
        config: U2MagicConfig
    ) -> Optional[bytes]:
        """下载种子文件"""
        # 检查重复下载间隔
        min_add_interval = config.min_add_interval if hasattr(config, 'min_add_interval') else 0
        if tid in self.tid_add_time:
            if time() - self.tid_add_time[tid] < min_add_interval:
                logger.info(f"种子 {tid} 重复下载间隔不足")
                return None

        try:
            client = await self._get_client()
            headers = {
                "Cookie": config.cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            response = await client.get(download_link, headers=headers)
            response.raise_for_status()

            self._set_tid_add_time(tid, time())
            return response.content
        except Exception as e:
            logger.error(f"下载种子 {tid} 失败: {e}")
            return None

    def _parse_downloader_ids(self, config: U2MagicConfig) -> List[int]:
        """解析下载器ID列表"""
        downloader_ids = []

        # 先检查新的 downloader_ids 字段（多选）
        if hasattr(config, 'downloader_ids') and config.downloader_ids:
            try:
                ids = json.loads(config.downloader_ids)
                if isinstance(ids, list):
                    downloader_ids = [int(i) for i in ids if i]
            except (json.JSONDecodeError, TypeError, ValueError):
                # 尝试按逗号分隔解析
                try:
                    downloader_ids = [int(i.strip()) for i in config.downloader_ids.split(',') if i.strip()]
                except ValueError:
                    pass

        # 如果没有多选，回退到单选的 downloader_id
        if not downloader_ids and config.downloader_id:
            downloader_ids = [config.downloader_id]

        return downloader_ids

    async def _get_downloader_free_space(self, downloader: 'Downloader') -> int:
        """获取下载器可用空间（字节）"""
        try:
            async with downloader_client(downloader) as client:
                if not client:
                    return 0
                # 优先使用 get_free_space 方法
                if hasattr(client, 'get_free_space'):
                    return await client.get_free_space()
                # 尝试从 get_stats 获取
                if hasattr(client, 'get_stats'):
                    stats = await client.get_stats()
                    if stats and hasattr(stats, 'free_space'):
                        return int(stats.free_space)
        except Exception as e:
            logger.debug(f"获取下载器 {downloader.name} 可用空间失败: {e}")
        return 0

    async def _select_best_downloader(
        self,
        downloader_ids: List[int],
        torrent_size: int
    ) -> Optional['Downloader']:
        """根据种子大小选择最佳下载器

        策略：
        1. 获取所有下载器的可用空间
        2. 优先选择空间足够的下载器（需要1.5倍种子大小的余量）
        3. 如果都不够，选择空间最大的下载器
        """
        if not downloader_ids:
            return None

        # 获取所有下载器
        result = await self.db.execute(
            select(Downloader).where(Downloader.id.in_(downloader_ids))
        )
        downloaders = result.scalars().all()

        if not downloaders:
            return None

        # 只有一个下载器时直接返回
        if len(downloaders) == 1:
            return downloaders[0]

        # 获取各下载器可用空间
        downloader_spaces = []
        required_space = int(torrent_size * 1.5)  # 需要1.5倍余量

        for downloader in downloaders:
            free_space = await self._get_downloader_free_space(downloader)
            downloader_spaces.append({
                'downloader': downloader,
                'free_space': free_space,
                'has_enough': free_space >= required_space
            })
            logger.debug(
                f"下载器 {downloader.name}: 可用空间 {free_space / (1024**3):.2f}GB, "
                f"需要 {required_space / (1024**3):.2f}GB, "
                f"{'足够' if free_space >= required_space else '不足'}"
            )

        # 按空间排序
        downloader_spaces.sort(key=lambda x: x['free_space'], reverse=True)

        # 优先选择空间足够的下载器（从空间最大的开始）
        for item in downloader_spaces:
            if item['has_enough']:
                logger.info(
                    f"选择下载器 {item['downloader'].name} "
                    f"(可用空间 {item['free_space'] / (1024**3):.2f}GB)"
                )
                return item['downloader']

        # 都不够，选择空间最大的
        if downloader_spaces:
            best = downloader_spaces[0]
            logger.warning(
                f"所有下载器空间都不足，选择空间最大的 {best['downloader'].name} "
                f"(可用空间 {best['free_space'] / (1024**3):.2f}GB)"
            )
            return best['downloader']

        return None

    async def add_to_downloader(
        self,
        torrent_data: bytes,
        config: U2MagicConfig,
        torrent_size: int = 0
    ) -> bool:
        """添加种子到下载器（支持多下载器智能分配）

        Args:
            torrent_data: 种子文件数据
            config: U2追魔配置
            torrent_size: 种子大小（字节），用于智能分配

        Returns:
            是否成功添加
        """
        # 解析下载器ID列表
        downloader_ids = self._parse_downloader_ids(config)

        if not downloader_ids:
            # 保存到监控目录
            if config.watch_dir:
                try:
                    import hashlib
                    hash_name = hashlib.md5(torrent_data[:1024]).hexdigest()[:8]
                    path = os.path.join(config.watch_dir, f"u2_{hash_name}.torrent")
                    os.makedirs(config.watch_dir, exist_ok=True)
                    with open(path, 'wb') as f:
                        f.write(torrent_data)
                    return True
                except Exception as e:
                    logger.error(f"保存到监控目录失败: {e}")
            return False

        # 选择最佳下载器
        downloader = await self._select_best_downloader(downloader_ids, torrent_size)
        if not downloader:
            logger.error("没有可用的下载器")
            return False

        try:
            async with downloader_client(downloader) as client:
                if not client:
                    return False

                torrent_hash = await client.add_torrent(
                    torrent_data,
                    save_path=downloader.download_dir if downloader.download_dir else None,
                )

                if torrent_hash:
                    logger.info(f"种子已添加到下载器 {downloader.name}")
                    return True
                return False
        except Exception as e:
            logger.error(f"添加种子到下载器 {downloader.name} 失败: {e}")
            return False

    async def backup_torrent(
        self,
        torrent_data: bytes,
        tid: str,
        backup_dir: str
    ):
        """备份种子文件"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            path = os.path.join(backup_dir, f"[U2].{tid}.torrent")
            with open(path, 'wb') as f:
                f.write(torrent_data)
        except Exception as e:
            logger.error(f"备份种子失败: {e}")

    async def process_magic(self) -> Dict[str, Any]:
        """处理魔法列表"""
        config = await self.get_config()
        if not config or not config.enabled:
            return {"enabled": False, "total": 0, "downloaded": 0}

        if not config.cookie:
            logger.warning("U2 Cookie未配置")
            return {"enabled": True, "total": 0, "downloaded": 0, "error": "Cookie未配置"}

        # 加载状态
        await self.load_state()

        # 获取魔法列表（优先API）
        magic_list = []
        if config.api_token:
            magic_list = await self.fetch_magic_from_api(config)

        if not magic_list:
            magic_list = await self.fetch_magic_from_web(config)

        self.first_time = False

        # 保存状态
        await self.save_state()

        if not magic_list:
            return {"enabled": True, "total": 0, "downloaded": 0}

        # 处理每个魔法
        total = len(magic_list)
        downloaded = 0

        for magic_id, tid in magic_list:
            try:
                # 检查是否已存在记录
                result = await self.db.execute(
                    select(U2MagicRecord).where(
                        U2MagicRecord.torrent_id == str(tid)
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    self.checked.append(magic_id)
                    continue

                # 分析魔法
                info = await self.analyze_magic(magic_id, tid, config)

                if info:
                    # 下载种子
                    torrent_data = await self.download_torrent(
                        info['download_link'],
                        str(tid),
                        config
                    )

                    if torrent_data:
                        # 备份
                        if config.backup_dir:
                            await self.backup_torrent(torrent_data, str(tid), config.backup_dir)

                        # 添加到下载器（传递种子大小用于智能分配）
                        torrent_size = info.get('size', 0)
                        success = await self.add_to_downloader(torrent_data, config, torrent_size)

                        if success:
                            downloaded += 1
                            logger.info(f"下载种子 {tid}: {info['name'][:50]}")

                            # 创建记录
                            record = U2MagicRecord(
                                torrent_id=str(tid),
                                torrent_name=info['name'],
                                magic_type=info.get('magic_type', ''),
                                seeders=info.get('seeders', 0),
                                size=info.get('size', 0),
                                downloaded=True,
                                download_time=datetime.utcnow(),
                            )
                            self.db.add(record)
                        else:
                            record = U2MagicRecord(
                                torrent_id=str(tid),
                                torrent_name=info['name'],
                                magic_type=info.get('magic_type', ''),
                                seeders=info.get('seeders', 0),
                                size=info.get('size', 0),
                                downloaded=False,
                                skip_reason="添加到下载器失败",
                            )
                            self.db.add(record)
                    else:
                        record = U2MagicRecord(
                            torrent_id=str(tid),
                            torrent_name=info['name'],
                            magic_type=info.get('magic_type', ''),
                            seeders=info.get('seeders', 0),
                            size=info.get('size', 0),
                            downloaded=False,
                            skip_reason="下载种子文件失败",
                        )
                        self.db.add(record)

                self.checked.append(magic_id)

            except Exception as e:
                logger.error(f"处理魔法 {magic_id} 失败: {e}")

        await self.db.commit()
        await self.save_state()

        return {
            "enabled": True,
            "total": total,
            "downloaded": downloaded,
        }
