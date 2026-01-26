"""
单元测试 - RSS Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.rss_service import RssService


class TestUrlParsing:
    """测试 URL 解析"""

    def test_normalize_url_with_base(self):
        """测试相对 URL 转绝对 URL"""
        service = RssService.__new__(RssService)

        base_url = "https://example.com/rss"
        relative_url = "/download/123.torrent"

        result = service._normalize_url(relative_url, base_url)
        assert result == "https://example.com/download/123.torrent"

    def test_normalize_url_absolute(self):
        """测试绝对 URL 保持不变"""
        service = RssService.__new__(RssService)

        base_url = "https://example.com/rss"
        absolute_url = "https://other.com/download/123.torrent"

        result = service._normalize_url(absolute_url, base_url)
        assert result == "https://other.com/download/123.torrent"

    def test_is_magnet_link(self):
        """测试磁力链接识别"""
        service = RssService.__new__(RssService)

        assert service._is_magnet("magnet:?xt=urn:btih:abc123") is True
        assert service._is_magnet("https://example.com/file.torrent") is False

    def test_merge_passkey_params(self):
        """测试 passkey 参数合并"""
        service = RssService.__new__(RssService)

        feed_url = "https://example.com/rss?passkey=abc123"
        torrent_url = "https://example.com/download/123.torrent"

        result = service._merge_passkey(torrent_url, feed_url)
        assert "passkey=abc123" in result


class TestFilterLogic:
    """测试过滤逻辑"""

    def test_filter_by_size_min(self):
        """测试最小体积过滤"""
        service = RssService.__new__(RssService)

        feed = MagicMock()
        feed.min_size = 1073741824  # 1 GB

        # 500 MB 种子应该被过滤
        assert service._check_size_filter(536870912, feed) is False
        # 2 GB 种子应该通过
        assert service._check_size_filter(2147483648, feed) is True

    def test_filter_by_size_max(self):
        """测试最大体积过滤"""
        service = RssService.__new__(RssService)

        feed = MagicMock()
        feed.min_size = 0
        feed.max_size = 10737418240  # 10 GB

        # 5 GB 种子应该通过
        assert service._check_size_filter(5368709120, feed) is True
        # 20 GB 种子应该被过滤
        assert service._check_size_filter(21474836480, feed) is False

    def test_filter_by_keyword_include(self):
        """测试关键词包含过滤"""
        service = RssService.__new__(RssService)

        feed = MagicMock()
        feed.include_keywords = "1080p,BluRay"
        feed.exclude_keywords = ""

        assert service._check_keyword_filter("Movie.2024.1080p.BluRay", feed) is True
        assert service._check_keyword_filter("Movie.2024.720p.WEB", feed) is False

    def test_filter_by_keyword_exclude(self):
        """测试关键词排除过滤"""
        service = RssService.__new__(RssService)

        feed = MagicMock()
        feed.include_keywords = ""
        feed.exclude_keywords = "CAM,HDTS"

        assert service._check_keyword_filter("Movie.2024.1080p.BluRay", feed) is True
        assert service._check_keyword_filter("Movie.2024.CAM", feed) is False

    def test_filter_by_seeders(self):
        """测试做种人数过滤"""
        service = RssService.__new__(RssService)

        feed = MagicMock()
        feed.min_seeders = 5

        assert service._check_seeder_filter(10, feed) is True
        assert service._check_seeder_filter(3, feed) is False


class TestFreeDetection:
    """测试 Free 种子检测"""

    def test_detect_free_in_title(self):
        """测试标题中的 Free 标记"""
        service = RssService.__new__(RssService)

        assert service._is_free_torrent("[Free] Movie.2024.1080p", None) is True
        assert service._is_free_torrent("Movie.2024.1080p [2xFree]", None) is True
        assert service._is_free_torrent("Movie.2024.1080p", None) is False

    def test_detect_free_in_description(self):
        """测试描述中的 Free 标记"""
        service = RssService.__new__(RssService)

        description = "<span class='free'>Free</span>"
        assert service._is_free_torrent("Movie.2024.1080p", description) is True

        description = "Normal torrent"
        assert service._is_free_torrent("Movie.2024.1080p", description) is False


class TestHrDetection:
    """测试 HR 种子检测"""

    def test_detect_hr_in_title(self):
        """测试标题中的 HR 标记"""
        service = RssService.__new__(RssService)

        assert service._is_hr_torrent("[HR] Movie.2024.1080p", None) is True
        assert service._is_hr_torrent("Movie.2024.1080p [H&R]", None) is True
        assert service._is_hr_torrent("Movie.2024.1080p", None) is False

    def test_detect_hr_in_description(self):
        """测试描述中的 HR 标记"""
        service = RssService.__new__(RssService)

        description = "<span class='hitandrun'>H&R</span>"
        assert service._is_hr_torrent("Movie.2024.1080p", description) is True
