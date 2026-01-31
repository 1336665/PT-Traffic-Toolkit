"""
单元测试 - DeleteService 删种服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.delete_service import DeleteService


class TestConditionEvaluation:
    """测试条件评估逻辑"""

    def test_compare_number_greater_than(self):
        """测试数值大于比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value(100, ">", 50) is True
        assert service._compare_value(50, ">", 100) is False
        assert service._compare_value(100, ">", 100) is False

    def test_compare_number_less_than(self):
        """测试数值小于比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value(50, "<", 100) is True
        assert service._compare_value(100, "<", 50) is False
        assert service._compare_value(100, "<", 100) is False

    def test_compare_number_equals(self):
        """测试数值相等比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value(100, "=", 100) is True
        assert service._compare_value(100, "==", 100) is True
        assert service._compare_value(100, "=", 50) is False

    def test_compare_number_greater_or_equal(self):
        """测试数值大于等于比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value(100, ">=", 50) is True
        assert service._compare_value(100, ">=", 100) is True
        assert service._compare_value(50, ">=", 100) is False

    def test_compare_number_less_or_equal(self):
        """测试数值小于等于比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value(50, "<=", 100) is True
        assert service._compare_value(100, "<=", 100) is True
        assert service._compare_value(100, "<=", 50) is False

    def test_compare_string_contains(self):
        """测试字符串包含比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value("hello world", "contains", "world") is True
        assert service._compare_value("hello world", "contains", "foo") is False

    def test_compare_string_not_contains(self):
        """测试字符串不包含比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value("hello world", "not_contains", "foo") is True
        assert service._compare_value("hello world", "not_contains", "world") is False

    def test_compare_string_starts_with(self):
        """测试字符串开头比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value("hello world", "starts_with", "hello") is True
        assert service._compare_value("hello world", "starts_with", "world") is False

    def test_compare_string_ends_with(self):
        """测试字符串结尾比较"""
        service = DeleteService.__new__(DeleteService)

        assert service._compare_value("hello world", "ends_with", "world") is True
        assert service._compare_value("hello world", "ends_with", "hello") is False


class TestUnitConversion:
    """测试单位转换"""

    def test_convert_size_bytes(self):
        """测试字节大小转换"""
        service = DeleteService.__new__(DeleteService)

        assert service._convert_size(1024, "KB") == 1024 * 1024
        assert service._convert_size(1, "MB") == 1024 * 1024
        assert service._convert_size(1, "GB") == 1024 * 1024 * 1024
        assert service._convert_size(100, "B") == 100

    def test_convert_time_seconds(self):
        """测试时间单位转换"""
        service = DeleteService.__new__(DeleteService)

        assert service._convert_time(1, "minutes") == 60
        assert service._convert_time(1, "hours") == 3600
        assert service._convert_time(1, "days") == 86400
        assert service._convert_time(60, "seconds") == 60


class TestConditionLogic:
    """测试条件逻辑组合"""

    def test_and_logic_all_true(self):
        """测试 AND 逻辑 - 全部为真"""
        service = DeleteService.__new__(DeleteService)

        conditions = [
            {"result": True},
            {"result": True},
            {"result": True},
        ]
        assert service._evaluate_logic(conditions, "and") is True

    def test_and_logic_one_false(self):
        """测试 AND 逻辑 - 一个为假"""
        service = DeleteService.__new__(DeleteService)

        conditions = [
            {"result": True},
            {"result": False},
            {"result": True},
        ]
        assert service._evaluate_logic(conditions, "and") is False

    def test_or_logic_one_true(self):
        """测试 OR 逻辑 - 一个为真"""
        service = DeleteService.__new__(DeleteService)

        conditions = [
            {"result": False},
            {"result": True},
            {"result": False},
        ]
        assert service._evaluate_logic(conditions, "or") is True

    def test_or_logic_all_false(self):
        """测试 OR 逻辑 - 全部为假"""
        service = DeleteService.__new__(DeleteService)

        conditions = [
            {"result": False},
            {"result": False},
            {"result": False},
        ]
        assert service._evaluate_logic(conditions, "or") is False


class TestFieldMapping:
    """测试字段映射"""

    def test_get_torrent_field_progress(self):
        """测试获取种子进度字段"""
        service = DeleteService.__new__(DeleteService)

        torrent = MagicMock()
        torrent.progress = 0.5

        value = service._get_torrent_field(torrent, "progress")
        assert value == 0.5

    def test_get_torrent_field_seeding_time(self):
        """测试获取做种时间字段"""
        service = DeleteService.__new__(DeleteService)

        torrent = MagicMock()
        torrent.seeding_time = 3600

        value = service._get_torrent_field(torrent, "seeding_time")
        assert value == 3600

    def test_get_torrent_field_ratio(self):
        """测试获取分享率字段"""
        service = DeleteService.__new__(DeleteService)

        torrent = MagicMock()
        torrent.ratio = 2.5

        value = service._get_torrent_field(torrent, "ratio")
        assert value == 2.5

    def test_get_torrent_field_tracker(self):
        """测试获取 Tracker 字段"""
        service = DeleteService.__new__(DeleteService)

        torrent = MagicMock()
        torrent.tracker = "https://tracker.example.com/announce"

        value = service._get_torrent_field(torrent, "tracker")
        assert value == "https://tracker.example.com/announce"
