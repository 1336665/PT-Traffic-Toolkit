"""
qBit Smart Limit - 完整移植版
基于 Speed-Limiting-Engine.py v11.0.0 PRO

核心功能:
- PID控制算法精准限速
- 卡尔曼滤波速度预测
- 自动汇报周期检测
- 多时间窗口速度追踪
- 自适应量化
- 强制汇报优化
"""

import asyncio
import time
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Deque
from collections import deque
from dataclasses import dataclass, field

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SpeedLimitConfig, SpeedLimitSite, SpeedLimitRecord, Downloader, SystemSettings
from app.services.downloader import create_downloader, TorrentInfo
from app.services.downloader.context import downloader_client
from app.utils import get_tracker_domain, get_logger

logger = get_logger('pt_manager.speed_limit')


# ════════════════════════════════════════════════════════════════════════════════
# 模块级缓存
# ════════════════════════════════════════════════════════════════════════════════
_status_cache: Dict[str, Any] = {}
_status_cache_time: float = 0
STATUS_CACHE_TTL: float = 2.0  # 状态缓存有效期（秒），2秒快速刷新
_cache_lock: asyncio.Lock = asyncio.Lock()  # 缓存访问锁，防止竞态条件

# TID缓存 (hash -> tid)，避免频繁访问PT站点
# 种子的TID不会变化，所以可以永久缓存
_tid_cache: Dict[str, str] = {}
MAX_TID_CACHE_SIZE: int = 1000  # TID缓存最大条目数

# 发布时间缓存 (hash -> publish_timestamp)，避免频繁访问PT站点
# 种子的发布时间不会变化，所以可以永久缓存
_publish_time_cache: Dict[str, float] = {}

# Peerlist时间缓存 (hash -> (fetch_time, idle_seconds))
# 缓存peerlist返回的空闲时间，避免频繁访问PT站点
# 读取时动态计算: 当前空闲时间 = 缓存空闲时间 + (当前时间 - 缓存时间)
_peerlist_cache: Dict[str, Tuple[float, int]] = {}
PEERLIST_CACHE_TTL: float = 120.0  # peerlist缓存有效期（秒），2分钟内不重复请求
MAX_PEERLIST_CACHE_SIZE: int = 500  # peerlist缓存最大条目数
PEERLIST_CACHE_EXPIRE: float = 3600.0  # peerlist缓存过期时间（秒），1小时后清理

# 种子comment URL缓存 (hash -> comment_url)，用于peerlist TID提取
# comment URL通常不会变化，可以长期缓存
_comment_cache: Dict[str, str] = {}
MAX_COMMENT_CACHE_SIZE: int = 1000

# 后台刷新标志，防止多次触发后台刷新
_background_refresh_running: bool = False

def cleanup_caches():
    """清理过期和超量的缓存，防止内存泄漏"""
    global _tid_cache, _peerlist_cache, _publish_time_cache, _comment_cache
    now = time.time()

    # 清理TID缓存（如果超过最大大小，保留最近的）
    if len(_tid_cache) > MAX_TID_CACHE_SIZE:
        # 由于dict保持插入顺序，保留最后插入的
        items = list(_tid_cache.items())
        _tid_cache = dict(items[-MAX_TID_CACHE_SIZE:])
        logger.debug(f"TID缓存已清理，当前条目数: {len(_tid_cache)}")

    # 清理发布时间缓存（与TID缓存保持同步大小）
    if len(_publish_time_cache) > MAX_TID_CACHE_SIZE:
        items = list(_publish_time_cache.items())
        _publish_time_cache = dict(items[-MAX_TID_CACHE_SIZE:])
        logger.debug(f"发布时间缓存已清理，当前条目数: {len(_publish_time_cache)}")

    # 清理过期的peerlist缓存
    expired_keys = [
        k for k, (fetch_time, _) in _peerlist_cache.items()
        if now - fetch_time > PEERLIST_CACHE_EXPIRE
    ]
    for k in expired_keys:
        del _peerlist_cache[k]
    if expired_keys:
        logger.debug(f"Peerlist缓存已清理 {len(expired_keys)} 条过期记录")

    # 如果peerlist缓存仍然过大，按时间排序删除最旧的
    if len(_peerlist_cache) > MAX_PEERLIST_CACHE_SIZE:
        items = sorted(_peerlist_cache.items(), key=lambda x: x[1][0])
        _peerlist_cache = dict(items[-MAX_PEERLIST_CACHE_SIZE:])
        logger.debug(f"Peerlist缓存已裁剪，当前条目数: {len(_peerlist_cache)}")

    # 清理comment缓存（如果超过最大大小，保留最近的）
    if len(_comment_cache) > MAX_COMMENT_CACHE_SIZE:
        items = list(_comment_cache.items())
        _comment_cache = dict(items[-MAX_COMMENT_CACHE_SIZE:])
        logger.debug(f"Comment缓存已清理，当前条目数: {len(_comment_cache)}")

# 共享 HTTP 客户端，用于访问 PT 站点（避免频繁创建连接）
_http_client: Optional[httpx.AsyncClient] = None

async def get_http_client() -> httpx.AsyncClient:
    """获取或创建共享的 HTTP 客户端"""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=15.0)
    return _http_client

async def close_http_client():
    """关闭共享的 HTTP 客户端（应在应用关闭时调用）"""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


# ════════════════════════════════════════════════════════════════════════════════
# 常量配置
# ════════════════════════════════════════════════════════════════════════════════
class C:
    """配置常量"""
    PHASE_WARMUP = "warmup"
    PHASE_CATCH = "catch"
    PHASE_STEADY = "steady"
    PHASE_FINISH = "finish"
    PHASE_IDLE = "idle"  # 新增：空闲阶段，不需要限速

    # 阶段时间阈值（秒）
    WARMUP_TIME = 60       # 延长预热时间到60秒
    FINISH_TIME = 30
    STEADY_TIME = 120

    # 精度阈值
    PRECISION_PERFECT = 0.001
    PRECISION_GOOD = 0.005

    # 速度保护
    SPEED_PROTECT_RATIO = 2.5
    SPEED_PROTECT_LIMIT = 1.3
    PROGRESS_PROTECT = 0.90

    # 最小限速值 (bytes)
    MIN_LIMIT = 4096

    # 汇报间隔估算（秒）
    ANNOUNCE_INTERVAL_NEW = 1800      # 新种30分钟
    ANNOUNCE_INTERVAL_WEEK = 2700     # 一周内45分钟
    ANNOUNCE_INTERVAL_OLD = 3600      # 旧种1小时
    # 允许的最大汇报剩余时间（秒）- 与用户脚本保持一致
    MAX_REANNOUNCE = 86400            # 1天

    # 强制汇报相关
    REANNOUNCE_WAIT_LIMIT = 5120      # 等待汇报时的限速 (KB)
    REANNOUNCE_MIN_INTERVAL = 900     # 最小汇报间隔（秒）
    REANNOUNCE_SPEED_SAMPLES = 300    # 速度采样数

    # 下载限速相关（参考 u2_magic.py limit_download_speed）
    MAX_AVG_UPLOAD_SPEED = 52428800   # 50M/s (bytes/s) - 两次汇报间平均上传速度上限
    DOWNLOAD_LIMIT_MIN_TIME = 2       # 开始检查下载限速的最小周期时间（秒）
    DOWNLOAD_LIMIT_ETA_FACTOR = 2     # 上传限速时的 ETA 检查因子
    DOWNLOAD_LIMIT_PEER_THRESHOLD = 20  # 检查 peer 进度时的阈值
    DOWNLOAD_LIMIT_ADJUST_UP = 1.5    # 下载限速值上调因子
    DOWNLOAD_LIMIT_ADJUST_DOWN = 1.5  # 下载限速值下调因子
    DOWNLOAD_LIMIT_MAX = 512000       # 最大下载限速值 (KB/s)

    # 汇报优化相关（参考 u2_magic.py optimize_announce_time）
    OPTIMIZE_DEQUE_LENGTH = 60        # 进度追踪队列长度（约5分钟，每5秒一条）
    OPTIMIZE_MIN_THIS_TIME = 30       # 开始优化的最小周期时间（秒）
    OPTIMIZE_WAIT_LIMIT = 5120        # 等待汇报时的限速值 (KB/s)

    # Kalman滤波参数
    KALMAN_Q_SPEED = 0.1
    KALMAN_Q_ACCEL = 0.05
    KALMAN_R = 0.5

    # 速度窗口（秒）
    SPEED_WINDOWS = [5, 15, 30, 60]

    # 窗口权重
    WINDOW_WEIGHTS = {
        'warmup': {5: 0.5, 15: 0.3, 30: 0.15, 60: 0.05},
        'catch': {5: 0.4, 15: 0.35, 30: 0.2, 60: 0.05},
        'steady': {5: 0.3, 15: 0.35, 30: 0.25, 60: 0.1},
        'finish': {5: 0.5, 15: 0.3, 30: 0.15, 60: 0.05},
        'idle': {5: 0.5, 15: 0.3, 30: 0.15, 60: 0.05},
    }

    # PID参数（按阶段）
    PID_PARAMS = {
        'warmup': {'kp': 0.3, 'ki': 0.05, 'kd': 0.02, 'headroom': 1.03},
        'catch': {'kp': 0.5, 'ki': 0.08, 'kd': 0.04, 'headroom': 1.02},
        'steady': {'kp': 0.7, 'ki': 0.10, 'kd': 0.05, 'headroom': 1.005},
        'finish': {'kp': 0.8, 'ki': 0.15, 'kd': 0.08, 'headroom': 1.002},
        'idle': {'kp': 0.3, 'ki': 0.05, 'kd': 0.02, 'headroom': 1.03},
    }

    # 量化步长
    QUANT_STEPS = {
        'warmup': 4096,
        'catch': 3072,
        'steady': 2048,
        'finish': 256,
        'idle': 8192,
    }

    # 周期进度阈值 - 调整为更严格
    PROGRESS_BEHIND_THRESHOLD = 0.90   # 进度落后阈值
    PROGRESS_AHEAD_THRESHOLD = 1.02    # 进度超前阈值（降低，更快触发限速）
    CATCH_UP_MULTIPLIER = 1.3          # 追赶时的速度倍数（降低，避免追赶时超速）

    # 限速启动阈值 - 调整为更积极
    LIMIT_START_PROGRESS = 0.5         # 当周期进度超过50%时就考虑限速
    LIMIT_START_PREDICTION = 1.02      # 当预测上传量超过目标102%时就限速（更敏感）
    NO_LIMIT_HEADROOM = 0.2            # 只有还有20%以上的配额余量时才可能不限速

    # 动态限速触发（参考 u2_magic.py：接近超标才开始限速，避免过早）
    LIMIT_TRIGGER_BUFFER_SEC = 10.0   # 反应/调度缓冲（秒），≈ res = 10 * speed
    LIMIT_TRIGGER_FLOOR_RATIO = 0.12  # 进入限速后的保守“底速”比例（≈6MiB/50MiB）
    LIMIT_TRIGGER_FLOOR_RATIO_MIN = 0.05
    LIMIT_TRIGGER_FLOOR_RATIO_MAX = 0.20


    # 动态循环间隔配置（秒）
    # 参考 Speed-Limiting-Engine.py: 根据最小剩余时间智能调整检查频率
    DYNAMIC_INTERVAL = {
        'critical': 0.2,    # 剩余 ≤5秒: 200ms
        'urgent': 0.5,      # 剩余 ≤15秒: 500ms
        'active': 1.0,      # 剩余 ≤30秒: 1秒
        'normal': 2.0,      # 剩余 ≤60秒: 2秒
        'relaxed': 3.0,     # 剩余 ≤120秒: 3秒
        'idle': 5.0,        # 剩余 >120秒: 5秒
    }
    DYNAMIC_INTERVAL_MIN = 0.2    # 最小间隔
    DYNAMIC_INTERVAL_MAX = 5.0    # 最大间隔


# ════════════════════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════════════════════
def safe_div(a: float, b: float, default: float = 0) -> float:
    """安全除法"""
    try:
        if b == 0 or abs(b) < 1e-10:
            return default
        return a / b
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在范围内"""
    return max(min_val, min(max_val, value))


def estimate_announce_interval(time_ref: float, min_interval: int = 300, seeding_time: int = 0, is_publish_time: bool = False) -> int:
    """根据种子时间估算汇报间隔 - 按照 u2_magic.py 的规则

    Args:
        time_ref: 种子发布时间或添加时间的时间戳
        min_interval: 最小汇报间隔（默认300秒）
        seeding_time: 做种时间（秒），当没有发布时间时用于估算种子年龄
        is_publish_time: time_ref是否为发布时间（发布时间优先级最高）

    Returns:
        估算的汇报间隔（秒）
    """
    # 计算种子年龄
    # 优先级: 发布时间 > 做种时间 > 添加时间
    now_ts = time.time()
    if is_publish_time and time_ref > 0:
        # 发布时间应当是过去时间；如果解析到未来（常见原因：抓到了促销结束时间或时区错误），直接忽略并走兜底
        if time_ref > now_ts + 60:
            is_publish_time = False
        else:
            # 发布时间是最准确的，直接计算年龄
            age = now_ts - time_ref
    if (not is_publish_time) and seeding_time > 0:
        # 做种时间可以作为种子年龄的下限估计
        # 如果做种时间很长，说明种子至少这么老
        age = seeding_time
    else:
        # 添加时间作为兜底
        age = now_ts - time_ref

    if age < 7 * 86400:  # 7天内
        return max(C.ANNOUNCE_INTERVAL_NEW, min_interval)  # 1800
    elif age < 30 * 86400:  # 30天内
        return max(C.ANNOUNCE_INTERVAL_WEEK, min_interval)  # 2700
    return max(C.ANNOUNCE_INTERVAL_OLD, min_interval)  # 3600


def get_phase(time_left: float, synced: bool, needs_limiting: bool = True) -> str:
    """根据剩余时间确定阶段"""
    if not needs_limiting:
        return C.PHASE_IDLE
    if not synced:
        return C.PHASE_WARMUP
    if time_left <= C.FINISH_TIME:
        return C.PHASE_FINISH
    if time_left <= C.STEADY_TIME:
        return C.PHASE_STEADY
    return C.PHASE_CATCH


# ════════════════════════════════════════════════════════════════════════════════
# 核心控制器
# ════════════════════════════════════════════════════════════════════════════════
class PIDController:
    """PID控制器 - 带阶段自适应参数"""

    def __init__(self):
        self.kp = 0.6
        self.ki = 0.15
        self.kd = 0.08
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = 0.0
        self._last_output = 1.0
        self._initialized = False
        self._integral_limit = 0.4
        self._derivative_filter = 0.0

    def set_phase(self, phase: str):
        """设置阶段并更新PID参数"""
        params = C.PID_PARAMS.get(phase, C.PID_PARAMS['steady'])
        self.kp = params['kp']
        self.ki = params['ki']
        self.kd = params['kd']

    def update(self, setpoint: float, measured: float, now: float) -> float:
        """计算PID输出"""
        error = safe_div(setpoint - measured, max(setpoint, 1), 0)

        if not self._initialized:
            self._last_error = error
            self._last_time = now
            self._initialized = True
            return 1.0

        dt = now - self._last_time
        if dt <= 0.01:
            return self._last_output
        self._last_time = now

        # 比例项
        p_term = self.kp * error

        # 积分项（带抗饱和）
        self._integral = clamp(
            self._integral + error * dt,
            -self._integral_limit,
            self._integral_limit
        )
        i_term = self.ki * self._integral

        # 微分项（带滤波）
        raw_derivative = (error - self._last_error) / dt
        self._derivative_filter = 0.3 * raw_derivative + 0.7 * self._derivative_filter
        d_term = self.kd * self._derivative_filter
        self._last_error = error

        output = clamp(1.0 + p_term + i_term + d_term, 0.5, 2.0)
        self._last_output = output
        return output

    def reset(self):
        """重置控制器"""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = 0.0
        self._last_output = 1.0
        self._derivative_filter = 0.0
        self._initialized = False

    def get_state(self) -> Dict:
        return {
            'integral': self._integral,
            'last_error': self._last_error,
            'last_time': self._last_time,
            'last_output': self._last_output,
            'derivative_filter': self._derivative_filter,
            'initialized': self._initialized,
        }

    def set_state(self, state: Dict):
        self._integral = state.get('integral', 0.0)
        self._last_error = state.get('last_error', 0.0)
        self._last_time = state.get('last_time', 0.0)
        self._last_output = state.get('last_output', 1.0)
        self._derivative_filter = state.get('derivative_filter', 0.0)
        self._initialized = state.get('initialized', False)


class ExtendedKalman:
    """扩展卡尔曼滤波器 - 带加速度估计"""

    def __init__(self):
        self.speed = 0.0
        self.accel = 0.0
        self.p00 = 1000.0
        self.p01 = 0.0
        self.p10 = 0.0
        self.p11 = 1000.0
        self._last_time = 0.0
        self._initialized = False

    def update(self, measurement: float, now: float) -> Tuple[float, float]:
        """更新滤波器，返回(速度, 加速度)"""
        if not self._initialized:
            self.speed = measurement
            self._last_time = now
            self._initialized = True
            return measurement, 0.0

        dt = now - self._last_time
        if dt <= 0.01:
            return self.speed, self.accel
        self._last_time = now

        # 预测步骤
        pred_speed = self.speed + self.accel * dt
        p00_pred = self.p00 + dt * (self.p10 + self.p01) + dt * dt * self.p11 + C.KALMAN_Q_SPEED
        p01_pred = self.p01 + dt * self.p11
        p10_pred = self.p10 + dt * self.p11
        p11_pred = self.p11 + C.KALMAN_Q_ACCEL

        # 更新步骤
        s = p00_pred + C.KALMAN_R
        if abs(s) < 1e-10:
            return self.speed, self.accel

        k0 = p00_pred / s
        k1 = p10_pred / s
        innovation = measurement - pred_speed

        self.speed = pred_speed + k0 * innovation
        self.accel = self.accel + k1 * innovation
        self.p00 = (1 - k0) * p00_pred
        self.p01 = (1 - k0) * p01_pred
        self.p10 = -k1 * p00_pred + p10_pred
        self.p11 = -k1 * p01_pred + p11_pred

        return self.speed, self.accel

    def predict_upload(self, seconds: float) -> float:
        """预测未来上传量"""
        return max(0, self.speed * seconds + 0.5 * self.accel * seconds * seconds)

    def reset(self):
        self.speed = 0.0
        self.accel = 0.0
        self.p00 = 1000.0
        self.p01 = 0.0
        self.p10 = 0.0
        self.p11 = 1000.0
        self._initialized = False

    def get_state(self) -> Dict:
        return {
            'speed': self.speed,
            'accel': self.accel,
            'p00': self.p00, 'p01': self.p01,
            'p10': self.p10, 'p11': self.p11,
            'last_time': self._last_time,
            'initialized': self._initialized,
        }

    def set_state(self, state: Dict):
        self.speed = state.get('speed', 0.0)
        self.accel = state.get('accel', 0.0)
        self.p00 = state.get('p00', 1000.0)
        self.p01 = state.get('p01', 0.0)
        self.p10 = state.get('p10', 0.0)
        self.p11 = state.get('p11', 1000.0)
        self._last_time = state.get('last_time', 0.0)
        self._initialized = state.get('initialized', False)


class MultiWindowSpeedTracker:
    """多窗口速度追踪器 - 使用简单锁保护数据"""

    def __init__(self):
        self._samples: Deque[Tuple[float, float]] = deque(maxlen=1200)

    def record(self, now: float, speed: float):
        """记录速度采样"""
        self._samples.append((now, speed))

    def get_weighted_avg(self, now: float, phase: str) -> float:
        """获取加权平均速度"""
        weights = C.WINDOW_WEIGHTS.get(phase, C.WINDOW_WEIGHTS['steady'])
        samples = list(self._samples)

        total_weight = 0.0
        weighted_sum = 0.0

        for window in C.SPEED_WINDOWS:
            win_samples = [s for t, s in samples if now - t <= window]
            if win_samples:
                avg = sum(win_samples) / len(win_samples)
                w = weights.get(window, 0.25)
                weighted_sum += avg * w
                total_weight += w

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_recent_trend(self, now: float, window: int = 10) -> float:
        """获取最近的速度趋势"""
        samples = [(t, s) for t, s in self._samples if now - t <= window]

        if len(samples) < 5:
            return 0.0

        mid = len(samples) // 2
        first = sum(s for _, s in samples[:mid]) / mid
        second = sum(s for _, s in samples[mid:]) / (len(samples) - mid)
        return safe_div(second - first, first, 0)

    def clear(self):
        self._samples.clear()

    def get_state(self) -> Dict:
        return {'samples': list(self._samples)}

    def set_state(self, state: Dict):
        self._samples = deque(state.get('samples', []), maxlen=1200)


class AdaptiveQuantizer:
    """自适应量化器"""

    @staticmethod
    def quantize(limit: int, phase: str, current_speed: float, target: float, trend: float = 0) -> int:
        if limit <= 0:
            return limit

        base = C.QUANT_STEPS.get(phase, 1024)
        ratio = safe_div(current_speed, target, 1)

        if phase == 'finish':
            step = 256
        elif ratio > 1.2:
            step = base * 2
        elif ratio > 1.05:
            step = base
        elif ratio > 0.8:
            step = base // 2
        else:
            step = base

        if abs(trend) > 0.1:
            step = max(256, step // 2)

        step = int(clamp(step, 256, 8192))
        return max(C.MIN_LIMIT, int((limit + step // 2) // step) * step)


class PrecisionTracker:
    """精度追踪器 - 记录历史达标率并自动校正系数

    参考 Speed-Limiting-Engine.py 的 PrecisionTracker
    通过历史达标率动态调整限速系数，提高精度
    """

    def __init__(self, target_precision: float = 0.98, history_size: int = 20):
        self.target_precision = target_precision  # 目标达标率
        self.history_size = history_size  # 历史记录大小
        self.history: Deque[float] = deque(maxlen=history_size)  # 达标率历史
        self.correction_factor: float = 1.0  # 校正系数
        self.total_cycles: int = 0  # 总周期数
        self.success_cycles: int = 0  # 成功周期数

    def record(self, actual_upload: float, target_upload: float) -> None:
        """记录一个周期的结果

        Args:
            actual_upload: 实际上传量
            target_upload: 目标上传量
        """
        if target_upload <= 0:
            return

        ratio = actual_upload / target_upload
        self.history.append(ratio)
        self.total_cycles += 1

        # 达标判定：在 95%-105% 范围内视为成功
        if 0.95 <= ratio <= 1.05:
            self.success_cycles += 1

        # 更新校正系数
        self._update_correction()

    def _update_correction(self) -> None:
        """更新校正系数 - 使用自适应步长"""
        if len(self.history) < 5:
            return

        # 计算平均达标率
        avg_ratio = sum(self.history) / len(self.history)

        # 计算偏差大小，用于自适应步长
        deviation = abs(avg_ratio - 1.0)

        # 自适应步长：偏差越大，调整越快
        # 偏差 < 5%: 步长 0.005
        # 偏差 5-10%: 步长 0.01
        # 偏差 10-20%: 步长 0.02
        # 偏差 > 20%: 步长 0.03
        if deviation < 0.05:
            step = 0.005
        elif deviation < 0.10:
            step = 0.01
        elif deviation < 0.20:
            step = 0.02
        else:
            step = 0.03

        # 如果平均超标，降低系数；如果平均不足，提高系数
        if avg_ratio > 1.02:
            # 超标，需要更保守
            self.correction_factor = max(0.90, self.correction_factor - step)
        elif avg_ratio < 0.95:
            # 不足，可以更激进
            self.correction_factor = min(1.10, self.correction_factor + step)
        else:
            # 在目标范围内，缓慢回归到1.0（使用较小步长）
            regression_step = step * 0.2  # 回归速度较慢
            if self.correction_factor < 1.0:
                self.correction_factor = min(1.0, self.correction_factor + regression_step)
            elif self.correction_factor > 1.0:
                self.correction_factor = max(1.0, self.correction_factor - regression_step)

    def get_correction(self) -> float:
        """获取当前校正系数"""
        return self.correction_factor

    def get_precision_rate(self) -> float:
        """获取历史达标率"""
        if self.total_cycles == 0:
            return 0.0
        return self.success_cycles / self.total_cycles

    def get_recent_avg(self) -> float:
        """获取近期平均达标率"""
        if not self.history:
            return 1.0
        return sum(self.history) / len(self.history)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'correction_factor': self.correction_factor,
            'total_cycles': self.total_cycles,
            'success_cycles': self.success_cycles,
            'history': list(self.history),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrecisionTracker':
        """从字典反序列化"""
        tracker = cls()
        tracker.correction_factor = data.get('correction_factor', 1.0)
        tracker.total_cycles = data.get('total_cycles', 0)
        tracker.success_cycles = data.get('success_cycles', 0)
        for ratio in data.get('history', []):
            tracker.history.append(ratio)
        return tracker


class SmoothLimiter:
    """平滑限速器 - 参照用户提供的 qBit Smart Limit v10.9.1

    规则:
    - 收尾阶段不做平滑（直接跟随）
    - 变化 <20% 直接更新
    - 20%~50% 做 0.7/0.3 平滑
    - >50% 做 0.5/0.5 平滑
    """

    def __init__(self):
        self._smooth_limit: int = 0

    def smooth(self, new_limit: int, current_speed: float = 0, phase: str = "", now: float = 0) -> int:
        # new_limit <= 0 表示无限速
        if new_limit <= 0 or self._smooth_limit <= 0:
            self._smooth_limit = new_limit
            return new_limit

        # 收尾阶段直接跟随，避免迟滞
        if phase == C.PHASE_FINISH:
            self._smooth_limit = new_limit
            return new_limit

        change = abs(new_limit - self._smooth_limit) / max(self._smooth_limit, 1)

        if change < 0.2:
            self._smooth_limit = new_limit
        elif change < 0.5:
            self._smooth_limit = int(self._smooth_limit * 0.7 + new_limit * 0.3)
        else:
            self._smooth_limit = int(self._smooth_limit * 0.5 + new_limit * 0.5)

        return max(C.MIN_LIMIT, self._smooth_limit)

    def reset(self) -> None:
        """重置状态"""
        self._smooth_limit = 0


# ════════════════════════════════════════════════════════════════════════════════
# 种子状态管理
# ════════════════════════════════════════════════════════════════════════════════
@dataclass
class TorrentState:
    """单个种子的限速状态"""
    hash: str
    name: str
    tracker: str

    # 基本信息
    time_added: float = 0.0
    total_size: int = 0
    publish_time: Optional[float] = None
    seeding_time: int = 0  # 做种时间（秒），用于估算种子年龄

    # 上传量追踪
    total_uploaded: int = 0
    # 统计：用于计算本次循环增量（写入 SpeedLimitRecord）
    last_record_uploaded: int = 0
    last_record_downloaded: int = 0
    cycle_start_uploaded: int = 0
    cycle_synced: bool = False
    cycle_interval: float = 0.0
    last_jump: float = 0.0
    cycle_start_time: float = 0.0  # 周期开始时间

    # 汇报状态
    last_announce_time: Optional[float] = None
    last_reannounce: float = 0.0
    reannounced_this_cycle: bool = False
    waiting_reannounce: bool = False
    next_announce_time: Optional[float] = None
    announce_interval: Optional[int] = None
    min_announce: Optional[int] = None  # tracker min announce（秒），用于持久化/调试
    # next_announce 是否可靠（用于处理部分 libtorrent/qB 显示异常）
    next_announce_is_true: bool = False
    # next_announce 观测（用于检测跳变/异常）
    last_next_remaining: Optional[float] = None
    last_next_update_time: float = 0.0
    next_jump_suspect_count: int = 0

    # reannounce 缓存（完全按用户脚本逻辑：cached_tl/cache_ts -> 剩余时间）
    cached_tl: float = 0.0            # 上次采集到的“剩余秒数”
    cache_ts: float = 0.0             # 上次采集时间戳（time.time()）
    prev_tl: float = 0.0              # 上一轮剩余时间（用于检测跳变）
    jump_count: int = 0               # 检测到的周期跳变次数
    cycle_index: int = 0              # 周期编号（调试用途）
    interval_samples: Deque[float] = field(default_factory=lambda: deque(maxlen=5))


    # 控制器
    pid: PIDController = field(default_factory=PIDController)
    kalman: ExtendedKalman = field(default_factory=ExtendedKalman)
    tracker_speed: MultiWindowSpeedTracker = field(default_factory=MultiWindowSpeedTracker)
    precision_tracker: PrecisionTracker = field(default_factory=PrecisionTracker)  # 精度追踪器
    smooth_limiter: SmoothLimiter = field(default_factory=SmoothLimiter)  # 平滑限速器

    # 当前状态
    current_limit: int = 0
    phase: str = C.PHASE_WARMUP

    # 周期进度追踪
    cycle_target_upload: float = 0.0      # 本周期目标上传量
    cycle_current_upload: float = 0.0     # 本周期已上传量
    cycle_progress: float = 0.0           # 上传进度 (已上传/目标上传)
    cycle_time_progress: float = 0.0      # 时间进度 (已过时间/汇报间隔)
    cycle_avg_speed: float = 0.0          # 周期平均速度
    estimated_completion: float = 0.0     # 预估完成率

    # 下载限速相关（参考 u2_magic.py）
    current_download_limit: int = 0       # 当前下载限速值 (KB/s), -1=无限制
    current_upload_limit: int = 0         # 当前上传限速值 (KB/s), -1=无限制
    total_done: int = 0                   # 已下载完成量 (bytes)
    total_size_torrent: int = 0           # 种子总大小 (bytes)
    download_speed: float = 0             # 当前下载速度 (bytes/s)
    eta: int = 0                          # 预估完成时间（秒）
    uploaded_before: int = 0              # 上次汇报时的上传量
    detail_progress: Deque = field(default_factory=lambda: deque(maxlen=60))  # 详细进度追踪 [(uploaded, done, time), ...]
    waiting_for_reannounce: bool = False  # 是否正在等待强制汇报
    last_force_reannounce: float = 0      # 上次强制汇报时间

    def get_time_left(self, now: float) -> float:
        """获取距离下次汇报的剩余时间 - 完全按照用户提供脚本实现。

        用户脚本逻辑（qBit Smart Limit）：
        1) 若已知 last_announce_time：next = last_announce_time + interval
        2) 否则使用 cached_tl/cache_ts 计算：cached_tl - (now - cache_ts)
        3) 无可用数据返回 9999（表示未知）
        """
        if self.last_announce_time and self.last_announce_time > 0:
            interval = self.get_announce_interval()
            next_announce = self.last_announce_time + interval
            return max(0.0, next_announce - now)

        if self.cache_ts <= 0:
            return 9999.0

        return max(0.0, self.cached_tl - (now - self.cache_ts))

    def get_this_time(self, now: float) -> float:
        """获取本周期已过时间（秒）- 与用户脚本一致：elapsed(now)"""
        if self.cycle_start_time <= 0:
            return 0.0
        return max(0.0, now - self.cycle_start_time)

    def _estimate_interval(self) -> int:
        """估算汇报间隔，优先使用发布时间来判断种子年龄"""
        if self.publish_time and self.publish_time > 0:
            return estimate_announce_interval(self.publish_time, seeding_time=self.seeding_time, is_publish_time=True)
        return estimate_announce_interval(self.time_added, seeding_time=self.seeding_time, is_publish_time=False)

    def get_announce_interval(self) -> int:
        """获取汇报间隔 - 按照 u2_magic.py 的规则

        优先级:
        1. 使用已同步的周期间隔
        2. 使用客户端提供的 announce_interval
        3. 根据种子年龄估算（优先使用发布时间）
        """
        # 如果已同步周期，使用同步的间隔
        if self.cycle_synced and self.cycle_interval > 0:
            return int(self.cycle_interval)

        # 如果客户端提供了间隔
        if self.announce_interval and self.announce_interval > 0:
            return self.announce_interval

        # 根据种子发布时间估算（优先）或添加时间，使用做种时间辅助判断
        if self.publish_time and self.publish_time > 0:
            return estimate_announce_interval(self.publish_time, seeding_time=self.seeding_time, is_publish_time=True)

        return estimate_announce_interval(self.time_added, seeding_time=self.seeding_time, is_publish_time=False)

    def sync_cycle(self, total_uploaded: int, now: float, next_announce: Optional[float] = None, interval: Optional[int] = None):
        """同步汇报周期（按用户脚本逻辑）

        关键点：
        - 使用 qB 提供的 reannounce/next_announce（我们在外层已经标准化为“下一次汇报时间戳”）
          计算出 *剩余秒数*，缓存为 cached_tl/cache_ts。
        - 通过“剩余时间突然变大”来判断周期跳变（announce 完成后 reannounce 会重置）。
        - U2 的汇报间隔并非绝对固定：我们会在检测到多次跳变后，用实测间隔来更新 cycle_interval。
        """

        self.total_uploaded = total_uploaded

        # 1) 记录客户端给的 interval（避免误用 min_announce，必须 >=300s）
        if interval and interval >= 300:
            self.announce_interval = int(interval)
            # 如果还没有任何周期同步信息，用 tracker interval 作为初值
            if not self.cycle_synced or self.cycle_interval <= 0:
                self.cycle_interval = float(interval)
                self.cycle_synced = True

        # 2) 更新 next_announce_time，并缓存“剩余秒数”（cached_tl/cache_ts）
        if next_announce is not None and next_announce > 0:
            # next_announce 既可能是 unix 时间戳（推荐），也可能是剩余秒数（部分客户端/实现）。
            try:
                na = float(next_announce)
            except (TypeError, ValueError):
                na = 0.0

            remaining = 0.0
            if na > 0:
                # 经验阈值：unix 时间戳一般 > 1e9（2001 年以后）；小于该值基本可视作 “剩余秒数”。
                if na < 1_000_000_000:
                    remaining = na
                    self.next_announce_time = now + remaining
                else:
                    self.next_announce_time = na
                    remaining = na - now

            # 只缓存合理范围内的剩余时间，避免异常值污染。
            if 0 < remaining < C.MAX_REANNOUNCE:
                self.cached_tl = float(remaining)
                self.cache_ts = now

        # 3) 使用 cached_tl/cache_ts 计算当前剩余时间（用于跳变检测）
        tl_prop: Optional[float] = None
        if self.cache_ts > 0:
            tl_prop = max(0.0, self.cached_tl - (now - self.cache_ts))

        is_jump = False
        if tl_prop is not None and self.prev_tl > 0 and tl_prop > self.prev_tl + 30:
            is_jump = True

        # 4) 初始化周期 / 检测到跳变则开启新周期
        if self.cycle_start_time <= 0:
            self._start_new_cycle(total_uploaded, now, tl_prop, is_jump=False)
        elif is_jump:
            self._start_new_cycle(total_uploaded, now, tl_prop, is_jump=True)

        # 5) 更新 prev_tl
        if tl_prop is not None:
            self.prev_tl = tl_prop

    def _start_new_cycle(self, total_uploaded: int, now: float, tl: Optional[float], is_jump: bool):
        """开始/重置周期（参考用户脚本 TorrentState.new_cycle）"""

        # 记录上一个周期的精度数据（如果有有效数据）
        if is_jump and self.cycle_target_upload > 0 and self.cycle_current_upload > 0:
            self.precision_tracker.record(self.cycle_current_upload, self.cycle_target_upload)
            precision_rate = self.precision_tracker.get_precision_rate()
            correction = self.precision_tracker.get_correction()
            logger.info(
                f"[{self.name[:20]}] 周期跳变: 进度={self.cycle_progress:.1%}, "
                f"达标率={precision_rate:.1%}, 校正系数={correction:.3f}"
            )

        announce_interval = self.get_announce_interval()

        if is_jump:
            # 1) 用跳变间隔来同步 cycle_interval（U2 可能不是固定值）
            if self.last_jump > 0:
                measured = now - self.last_jump
                # 忽略明显异常/强制汇报造成的假间隔
                if 300 <= measured <= C.MAX_REANNOUNCE and (now - self.last_force_reannounce) > 120:
                    self.interval_samples.append(measured)
                    if len(self.interval_samples) >= 2:
                        sorted_samples = sorted(self.interval_samples)
                        median = sorted_samples[len(sorted_samples) // 2]
                        # 允许 tracker interval 变化：以样本中位数为准
                        self.cycle_interval = float(median)
                        self.cycle_synced = True

            self.last_jump = now
            self.jump_count += 1
            self.cycle_index += 1

            # 2) 周期基准直接从当前 uploaded 开始
            self.cycle_start_uploaded = total_uploaded
            self.cycle_start_time = now
            self.last_announce_time = now
        else:
            # 初次初始化：估算“本周期开始上传量”，让限速更接近真实周期。
            tl_val = tl if tl is not None else float(announce_interval)

            elapsed_in_cycle = 0.0
            if announce_interval > 0 and 0 < tl_val < announce_interval:
                elapsed_in_cycle = announce_interval - tl_val

            # 估算周期开始时间（让 this_time 更合理）
            if elapsed_in_cycle > 0:
                self.cycle_start_time = now - elapsed_in_cycle
            else:
                self.cycle_start_time = now

            # 新种：如果刚添加且还没经历一个完整周期，认为从 0 开始更安全
            if self.time_added > 0 and (now - self.time_added) < announce_interval:
                self.cycle_start_uploaded = 0
            else:
                if elapsed_in_cycle > 60 and self.kalman.speed > 0:
                    estimated_start = total_uploaded - int(self.kalman.speed * elapsed_in_cycle)
                    self.cycle_start_uploaded = max(0, estimated_start)
                else:
                    self.cycle_start_uploaded = total_uploaded

            # 初次初始化不强行写 last_announce_time，让 get_time_left 优先使用 cached_tl/cache_ts。

        # 通用重置
        self.reannounced_this_cycle = False
        self.waiting_reannounce = False

        # 重置周期进度
        self.cycle_current_upload = 0
        self.cycle_progress = 0
        self.cycle_time_progress = 0
        self.cycle_avg_speed = 0
        self.estimated_completion = 0

        # 重置平滑限速器（新周期允许限速值重新调整）
        self.smooth_limiter.reset()

    def update_cycle_progress(self, target_speed: float, safety_margin: float = 0.1):
        """更新周期进度追踪 - 使用 cycle_start_time 计算 elapsed（更符合用户脚本）"""
        now = time.time()
        interval = self.get_announce_interval()

        time_left = self.get_time_left(now)
        # 对异常值做保护：UI/算法都希望 time_left 在 [0, interval] 内
        if interval > 0 and (time_left < 0 or time_left > interval):
            time_left = max(0.0, min(float(interval), float(time_left)))

        # 如果周期开始时间未初始化，尝试根据 time_left 反推
        if self.cycle_start_time <= 0:
            if interval > 0 and 0 < time_left < interval:
                self.cycle_start_time = now - (interval - time_left)
            else:
                self.cycle_start_time = now
            # cycle_start_uploaded 在 sync_cycle/_start_new_cycle 里会更准确，这里仅兜底
            if self.cycle_start_uploaded <= 0:
                self.cycle_start_uploaded = self.total_uploaded

        this_time = max(0.0, now - self.cycle_start_time)

        if interval > 0:
            self.cycle_time_progress = max(0.0, min(1.0, this_time / interval))
        else:
            self.cycle_time_progress = 0.0

        # 计算本周期已上传量
        self.cycle_current_upload = max(0, self.total_uploaded - self.cycle_start_uploaded)

        # 计算目标上传量（考虑安全余量）
        self.cycle_target_upload = target_speed * interval * (1 - safety_margin)

        # 计算上传进度
        if self.cycle_target_upload > 0:
            self.cycle_progress = self.cycle_current_upload / self.cycle_target_upload
        else:
            self.cycle_progress = 0

        # 计算周期平均速度
        if this_time > 0:
            self.cycle_avg_speed = self.cycle_current_upload / this_time
        else:
            # 如果刚开始，使用卡尔曼滤波的即时速度
            self.cycle_avg_speed = self.kalman.speed if self.kalman.speed > 0 else 0

        # 预估完成率
        if time_left > 0 and self.kalman.speed > 0:
            predicted_upload = self.kalman.predict_upload(time_left)
            total_expected = self.cycle_current_upload + predicted_upload
            if self.cycle_target_upload > 0:
                self.estimated_completion = total_expected / self.cycle_target_upload
            else:
                self.estimated_completion = 1.0
        else:
            self.estimated_completion = self.cycle_progress

    def reset_cycle(self):
        """重置周期"""
        self.cycle_start_uploaded = self.total_uploaded
        self.reannounced_this_cycle = False
        self.waiting_reannounce = False

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'hash': self.hash,
            'name': self.name,
            'tracker': self.tracker,
            'time_added': self.time_added,
            'total_size': self.total_size,
            'publish_time': self.publish_time,
            'total_uploaded': self.total_uploaded,
            'last_record_uploaded': self.last_record_uploaded,
            'last_record_downloaded': self.last_record_downloaded,
            'cycle_start_uploaded': self.cycle_start_uploaded,
            'cycle_synced': self.cycle_synced,
            'cycle_interval': self.cycle_interval,
            'last_jump': self.last_jump,
            'cycle_start_time': self.cycle_start_time,
            'last_announce_time': self.last_announce_time,
            'last_reannounce': self.last_reannounce,
            'last_force_reannounce': self.last_force_reannounce,
            'reannounced_this_cycle': self.reannounced_this_cycle,
            'waiting_reannounce': self.waiting_reannounce,
            'next_announce_time': self.next_announce_time,
            'announce_interval': self.announce_interval,
            'min_announce': self.min_announce,
            'next_announce_is_true': self.next_announce_is_true,
            'last_next_remaining': self.last_next_remaining,
            'last_next_update_time': self.last_next_update_time,
            'next_jump_suspect_count': self.next_jump_suspect_count,
            'cached_tl': self.cached_tl,
            'cache_ts': self.cache_ts,
            'prev_tl': self.prev_tl,
            'jump_count': self.jump_count,
            'cycle_index': self.cycle_index,
            'interval_samples': list(self.interval_samples),
            'seeding_time': self.seeding_time,
            'current_limit': self.current_limit,
            'phase': self.phase,
            'cycle_target_upload': self.cycle_target_upload,
            'cycle_current_upload': self.cycle_current_upload,
            'cycle_progress': self.cycle_progress,
            'cycle_time_progress': self.cycle_time_progress,
            'cycle_avg_speed': self.cycle_avg_speed,
            'estimated_completion': self.estimated_completion,
            'pid_state': self.pid.get_state(),
            'kalman_state': self.kalman.get_state(),
            'tracker_state': self.tracker_speed.get_state(),
            'precision_tracker': self.precision_tracker.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TorrentState':
        """从字典反序列化"""
        state = cls(
            hash=data['hash'],
            name=data['name'],
            tracker=data['tracker'],
            time_added=data.get('time_added', 0),
            total_size=data.get('total_size', 0),
            publish_time=data.get('publish_time'),
            total_uploaded=data.get('total_uploaded', 0),
            last_record_uploaded=data.get('last_record_uploaded', data.get('total_uploaded', 0)),
            last_record_downloaded=data.get('last_record_downloaded', 0),
            cycle_start_uploaded=data.get('cycle_start_uploaded', 0),
            cycle_synced=data.get('cycle_synced', False),
            cycle_interval=data.get('cycle_interval', 0),
            last_jump=data.get('last_jump', 0),
            cycle_start_time=data.get('cycle_start_time', 0),
            last_announce_time=data.get('last_announce_time'),
            last_reannounce=data.get('last_reannounce', 0),
            last_force_reannounce=data.get('last_force_reannounce', 0.0),
            reannounced_this_cycle=data.get('reannounced_this_cycle', False),
            waiting_reannounce=data.get('waiting_reannounce', False),
            next_announce_time=data.get('next_announce_time'),
            announce_interval=data.get('announce_interval'),
            min_announce=(int(data.get('min_announce')) if data.get('min_announce') is not None else None),
            next_announce_is_true=data.get('next_announce_is_true', False),
            last_next_remaining=data.get('last_next_remaining'),
            last_next_update_time=data.get('last_next_update_time', 0.0),
            next_jump_suspect_count=data.get('next_jump_suspect_count', 0),
            cached_tl=data.get('cached_tl', 0.0),
            cache_ts=data.get('cache_ts', 0.0),
            prev_tl=data.get('prev_tl', 0.0),
            jump_count=data.get('jump_count', 0),
            cycle_index=data.get('cycle_index', 0),
            seeding_time=data.get('seeding_time', 0),
            current_limit=data.get('current_limit', 0),
            phase=data.get('phase', C.PHASE_WARMUP),
            cycle_target_upload=data.get('cycle_target_upload', 0),
            cycle_current_upload=data.get('cycle_current_upload', 0),
            cycle_progress=data.get('cycle_progress', 0),
            cycle_time_progress=data.get('cycle_time_progress', 0),
            cycle_avg_speed=data.get('cycle_avg_speed', 0),
            estimated_completion=data.get('estimated_completion', 0),
        )

        if 'pid_state' in data:
            state.pid.set_state(data['pid_state'])
        if 'kalman_state' in data:
            state.kalman.set_state(data['kalman_state'])
        if 'tracker_state' in data:
            state.tracker_speed.set_state(data['tracker_state'])
        if 'precision_tracker' in data:
            state.precision_tracker = PrecisionTracker.from_dict(data['precision_tracker'])

        # interval_samples（deque）
        samples = data.get('interval_samples')
        if isinstance(samples, list):
            for s in samples[-state.interval_samples.maxlen:]:
                try:
                    v = float(s)
                    if v > 0:
                        state.interval_samples.append(v)
                except Exception:
                    continue

        return state


# ════════════════════════════════════════════════════════════════════════════════
# 强制汇报优化器
# ════════════════════════════════════════════════════════════════════════════════
class ReannounceOptimizer:
    """强制汇报优化器"""

    @staticmethod
    def should_reannounce(
        state: TorrentState,
        total_uploaded: int,
        total_done: int,
        target_speed: float,
        now: float
    ) -> Tuple[bool, str]:
        """判断是否需要强制汇报"""
        # 检查最小汇报间隔
        if state.last_reannounce > 0 and now - state.last_reannounce < C.REANNOUNCE_MIN_INTERVAL:
            return False, ""

        # 已汇报过本周期
        if state.reannounced_this_cycle:
            return False, ""

        # 计算剩余时间和上传量
        time_left = state.get_time_left(now)
        if time_left <= 0 or time_left > C.STEADY_TIME:
            return False, ""

        # 计算当前周期上传量
        cycle_uploaded = total_uploaded - state.cycle_start_uploaded

        # 预测到周期结束时的上传量
        predicted_upload = state.kalman.predict_upload(time_left)
        expected_total = cycle_uploaded + predicted_upload

        # 计算目标上传量
        announce_interval = state.get_announce_interval()
        target_upload = target_speed * announce_interval

        # 如果预测会超标，考虑提前汇报
        if expected_total > target_upload * 1.05:
            # 计算最佳汇报时间
            avg_speed = state.kalman.speed
            if avg_speed > 0:
                perfect_time = (target_upload - cycle_uploaded) / avg_speed
                if perfect_time < time_left * 0.5:
                    return True, "优化汇报"

        # 如果接近周期结束且进度良好
        if time_left < 60 and cycle_uploaded > target_upload * 0.9:
            return True, "周期结束汇报"

        return False, ""

    @staticmethod
    def check_waiting_reannounce(
        state: TorrentState,
        total_uploaded: int,
        now: float
    ) -> Tuple[bool, str]:
        """检查等待汇报状态"""
        if not state.waiting_reannounce:
            return False, ""

        # 检查速度是否已降低
        current_speed = state.kalman.speed
        if current_speed < C.REANNOUNCE_WAIT_LIMIT * 1024:
            return True, "速度已降低"

        return False, ""


# ════════════════════════════════════════════════════════════════════════════════
# 下载限速控制器（参考 u2_magic.py limit_download_speed）
# ════════════════════════════════════════════════════════════════════════════════
class DownloadSpeedLimiter:
    """下载限速控制器 - 防止两次汇报间平均上传速度超过 50M/s

    原理:
    - 当平均上传速度接近 50M/s 且快要完成时，通过限制下载速度来延长完成时间
    - 这样可以在下次汇报前有更多时间上传，避免汇报时超速
    """

    @staticmethod
    def calculate_download_limit(
        state: TorrentState,
        this_time: float,
        this_up: int,
        total_size: int,
        total_done: int,
        eta: int,
        current_download_limit: int,
        current_download_speed: float,
        min_time: int = 120
    ) -> Tuple[Optional[int], str]:
        """计算下载限速值

        Args:
            state: 种子状态
            this_time: 本周期已过时间（秒）
            this_up: 本周期已上传量（bytes）
            total_size: 种子总大小（bytes）
            total_done: 已下载完成量（bytes）
            eta: 预估完成时间（秒）
            current_download_limit: 当前下载限速值（KB/s），-1=无限制
            current_download_speed: 当前下载速度（bytes/s）
            min_time: 最小检查时间

        Returns:
            (limit_kb, reason): 限速值（KB/s，-1=解除限速，None=不变），原因
        """
        # 检查周期时间是否足够
        if this_time < C.DOWNLOAD_LIMIT_MIN_TIME:
            return None, ""

        # 计算当前平均上传速度
        avg_upload_speed = this_up / this_time if this_time > 0 else 0

        # 如果当前没有下载限速
        if current_download_limit == -1 or current_download_limit == 0:
            # 检查是否需要开始限速
            if avg_upload_speed > C.MAX_AVG_UPLOAD_SPEED:  # 平均速度超过 50M/s
                # 检查是否快要完成
                check_eta = min_time
                if state.current_upload_limit > 0:
                    # 如果已经在上传限速，用更长的检查时间
                    check_eta = min_time * C.DOWNLOAD_LIMIT_ETA_FACTOR

                if 0 < eta <= check_eta:
                    # 计算下载限速值
                    # 公式: remaining / (this_up/50M - this_time + 30)
                    # 目的: 让完成时间延长到平均速度降到 50M/s 以下
                    remaining = total_size - total_done
                    denominator = this_up / C.MAX_AVG_UPLOAD_SPEED - this_time + 30
                    if denominator > 0:
                        limit_kb = int(remaining / denominator / 1024)
                        limit_kb = max(1, min(limit_kb, C.DOWNLOAD_LIMIT_MAX))
                        return limit_kb, f"开始下载限速: 平均上传={avg_upload_speed/1024/1024:.1f}M/s, ETA={eta}s"

        else:
            # 已经有下载限速
            if avg_upload_speed >= C.MAX_AVG_UPLOAD_SPEED:
                # 平均速度仍然 >= 50M/s，调整限速值
                if current_download_speed / 1024 < 2 * current_download_limit:
                    remaining = total_size - total_done
                    denominator = this_up / C.MAX_AVG_UPLOAD_SPEED - this_time + 60
                    if denominator > 0:
                        new_limit_kb = int(remaining / denominator / 1024)
                        new_limit_kb = min(new_limit_kb, C.DOWNLOAD_LIMIT_MAX)

                        # 限制调整幅度
                        if new_limit_kb > current_download_limit * C.DOWNLOAD_LIMIT_ADJUST_UP:
                            new_limit_kb = int(current_download_limit * C.DOWNLOAD_LIMIT_ADJUST_UP)
                            return new_limit_kb, f"上调下载限速: {current_download_limit} -> {new_limit_kb}KB/s"
                        elif new_limit_kb < current_download_limit / C.DOWNLOAD_LIMIT_ADJUST_DOWN:
                            new_limit_kb = int(current_download_limit / C.DOWNLOAD_LIMIT_ADJUST_DOWN)
                            return new_limit_kb, f"下调下载限速: {current_download_limit} -> {new_limit_kb}KB/s"
            else:
                # 平均速度已降到 50M/s 以下，可以解除限速
                return -1, f"解除下载限速: 平均上传={avg_upload_speed/1024/1024:.1f}M/s < 50M/s"

        return None, ""


# ════════════════════════════════════════════════════════════════════════════════
# 汇报优化控制器（参考 u2_magic.py optimize_announce_time）
# ════════════════════════════════════════════════════════════════════════════════
class AnnounceOptimizer:
    """汇报时间优化器 - 最大化完成前的上传量

    原理:
    - 假设种子下载时间超过汇报周期，且每次汇报前都限速到平均 50M/s
    - 要获得最多上传量，需要使完成时间尽可能延后
    - 最后一次汇报时间有一个最佳点能使完成时间延长最多
    - 在合适的时间强制汇报来调整最后一次汇报时间
    """

    @staticmethod
    def should_optimize(
        state: TorrentState,
        this_time: float,
        this_up: int,
        announce_interval: int,
        now: float
    ) -> Tuple[bool, Optional[int], str]:
        """判断是否需要优化汇报时间

        Args:
            state: 种子状态
            this_time: 本周期已过时间（秒）
            this_up: 本周期已上传量（bytes）
            announce_interval: 汇报间隔（秒）
            now: 当前时间戳

        Returns:
            (should_act, limit_kb, reason):
            - should_act: 是否需要采取行动
            - limit_kb: 建议的上传限速值（KB/s），None表示强制汇报
            - reason: 原因说明
        """
        # 检查条件
        if this_time < C.OPTIMIZE_MIN_THIS_TIME:
            return False, None, ""

        # 如果已经在等待汇报状态，检查是否可以汇报
        if state.waiting_for_reannounce:
            if this_up / this_time < C.MAX_AVG_UPLOAD_SPEED and this_time >= C.REANNOUNCE_MIN_INTERVAL:
                return True, None, "等待汇报完成，执行强制汇报"
            return False, None, ""

        # 需要足够的进度数据
        if len(state.detail_progress) < C.OPTIMIZE_DEQUE_LENGTH:
            return False, None, ""

        # 计算近期平均速度
        progress_list = list(state.detail_progress)
        if len(progress_list) < 2:
            return False, None, ""

        first = progress_list[0]
        last = progress_list[-1]
        time_span = last[2] - first[2]
        if time_span <= 0:
            return False, None, ""

        avg_upload_speed = (last[0] - first[0]) / time_span  # bytes/s
        avg_download_speed = (last[1] - first[1]) / time_span  # bytes/s

        # 只有上传速度超过 50M/s 且下载速度大于 0 时才优化
        if avg_upload_speed <= C.MAX_AVG_UPLOAD_SPEED or avg_download_speed <= 0:
            return False, None, ""

        # 计算关键时间点
        remaining = state.total_size_torrent - state.total_done
        if remaining <= 0:
            return False, None, ""

        complete_time = remaining / avg_download_speed + now  # 预计完成时间
        perfect_time = complete_time - announce_interval * C.MAX_AVG_UPLOAD_SPEED / avg_upload_speed  # 最佳汇报时间

        # 计算最早能强制汇报且不超速的时间
        if this_up / this_time > C.MAX_AVG_UPLOAD_SPEED:
            earliest = (this_up - C.MAX_AVG_UPLOAD_SPEED * this_time) / (45 * 1024 * 1024) + now
        else:
            earliest = now

        # 检查最小汇报间隔
        cycle_start = now - this_time
        if earliest - cycle_start < C.REANNOUNCE_MIN_INTERVAL:
            return False, None, ""

        # 判断策略
        if earliest > perfect_time:
            if now >= earliest:
                # 可以立即汇报
                if (this_up + avg_upload_speed * 20) / this_time > C.MAX_AVG_UPLOAD_SPEED:
                    return True, None, "已到最早汇报时间，执行强制汇报"
                return False, None, ""

            if earliest < perfect_time + 60:
                # 最早时间接近最佳时间，设置等待限速
                return True, C.OPTIMIZE_WAIT_LIMIT, "设置等待限速，准备强制汇报"
            else:
                # 比较不同策略的上传量
                next_announce = state.get_time_left(now)
                _eta1 = complete_time - earliest
                if _eta1 < 120:
                    return False, None, ""

                earliest_up = (earliest - now + this_time) * C.MAX_AVG_UPLOAD_SPEED + _eta1 * avg_upload_speed
                default_up = announce_interval * C.MAX_AVG_UPLOAD_SPEED
                _eta2 = complete_time - (now + next_announce)
                if _eta2 > 0:
                    default_up += _eta2 * avg_upload_speed

                if earliest_up > default_up:
                    return True, C.OPTIMIZE_WAIT_LIMIT, f"强制汇报更优: {earliest_up/1024/1024:.1f}M > {default_up/1024/1024:.1f}M"

        return False, None, ""


# ════════════════════════════════════════════════════════════════════════════════
# 主服务类
# ════════════════════════════════════════════════════════════════════════════════
class SpeedLimiterService:
    """动态限速服务 - 完整版"""

    STATE_KEY = "speed_limiter_state"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.states: Dict[str, TorrentState] = {}
        self._running = False
        # next_announce 可靠性状态（按下载器维度，参考 u2_magic.py 的 ana/ana_updated）
        # - ana=True: next_announce 可信
        # - ana=False: next_announce 不可信，优先用 peerlist idle 反推
        # - ana=None: 未判定，继续观察
        self._ana_state: Dict[int, Dict[str, Any]] = {}
        self._FORCED_REANNOUNCE_INTERVAL: int = 900  # 强制汇报间隔（秒），用于识别 reannounce 偏差


    async def get_config(self) -> Optional[SpeedLimitConfig]:
        """获取配置"""
        result = await self.db.execute(select(SpeedLimitConfig).limit(1))
        return result.scalar_one_or_none()

    async def get_site_rules(self) -> List[SpeedLimitSite]:
        """获取站点规则"""
        result = await self.db.execute(
            select(SpeedLimitSite).where(SpeedLimitSite.enabled == True)
        )
        return result.scalars().all()

    async def save_state(self, commit: bool = True):
        """保存状态到数据库"""
        try:
            state_data = {
                hash: state.to_dict()
                for hash, state in self.states.items()
            }
            state_json = json.dumps(state_data)

            # 更新或创建设置记录
            result = await self.db.execute(
                select(SystemSettings).where(SystemSettings.key == self.STATE_KEY)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = state_json
            else:
                setting = SystemSettings(key=self.STATE_KEY, value=state_json)
                self.db.add(setting)

            if commit:
                await self.db.commit()
        except Exception as e:
            logger.error(f"保存限速状态失败: {e}")

    async def load_state(self):
        """从数据库加载状态"""
        try:
            result = await self.db.execute(
                select(SystemSettings).where(SystemSettings.key == self.STATE_KEY)
            )
            setting = result.scalar_one_or_none()

            if setting and setting.value:
                state_data = json.loads(setting.value)
                self.states = {
                    hash: TorrentState.from_dict(data)
                    for hash, data in state_data.items()
                }
                logger.info(f"已加载 {len(self.states)} 个种子状态")
        except Exception as e:
            logger.error(f"加载限速状态失败: {e}")
            self.states = {}

    def _get_or_create_state(self, torrent: TorrentInfo, tracker: str) -> TorrentState:
        """获取或创建种子状态"""
        if torrent.hash not in self.states:
            now = time.time()
            cached_tl = 0.0
            cache_ts = 0.0
            if torrent.next_announce_time and torrent.next_announce_time > 0:
                remaining = torrent.next_announce_time - now
                if 0 < remaining < C.MAX_REANNOUNCE:
                    cached_tl = float(remaining)
                    cache_ts = now
            self.states[torrent.hash] = TorrentState(
                hash=torrent.hash,
                name=torrent.name,
                tracker=tracker,
                time_added=torrent.added_time.timestamp() if torrent.added_time else now,
                total_size=torrent.size,
                total_uploaded=torrent.uploaded,
                last_record_uploaded=torrent.uploaded,
                last_record_downloaded=torrent.downloaded,
                next_announce_time=torrent.next_announce_time,
                announce_interval=torrent.announce_interval,
                seeding_time=torrent.seeding_time or 0,  # 添加做种时间用于估算种子年龄
                # reannounce 缓存（用于更准确的剩余时间计算）
                cached_tl=cached_tl,
                cache_ts=cache_ts,
                # 周期起点初始化为“未知”，交由 sync_cycle 根据 time_left 反推
                cycle_start_time=0.0,
                cycle_start_uploaded=torrent.uploaded,
            )
        else:
            # 只有当新值有效时才更新，避免覆盖已有的好值
            if torrent.next_announce_time and torrent.next_announce_time > 0:
                self.states[torrent.hash].next_announce_time = torrent.next_announce_time
            if torrent.announce_interval and torrent.announce_interval > 0:
                self.states[torrent.hash].announce_interval = torrent.announce_interval
            # 始终更新做种时间（它会随时间增加）
            if torrent.seeding_time and torrent.seeding_time > 0:
                self.states[torrent.hash].seeding_time = torrent.seeding_time
        return self.states[torrent.hash]

    async def _resolve_tracker_domain(self, client, torrent: TorrentInfo) -> Optional[str]:
        tracker = get_tracker_domain(torrent.tracker)
        if tracker:
            return tracker
        if hasattr(client, "get_torrent_trackers"):
            try:
                trackers = await client.get_torrent_trackers(torrent.hash)
                for tr in trackers:
                    tier = tr.get("tier", -1)
                    url = tr.get("url", "")
                    if tier < 0 or url.startswith("**"):
                        continue
                    tracker = get_tracker_domain(url)
                    if tracker:
                        return tracker
            except Exception as e:
                logger.debug(f"获取 tracker 域名失败: {e}")
        return None

    def _get_site_base_url(self, site_rule: SpeedLimitSite) -> Optional[str]:
        """从peerlist配置中提取站点基础URL

        支持两种格式:
        1. 完整模板: https://u2.dmhy.org/viewpeerlist.php?id={tid}
        2. 站点URL: https://u2.dmhy.org
        """
        url_config = site_rule.peerlist_url_template
        if not url_config:
            return None

        from urllib.parse import urlparse
        parsed = urlparse(url_config)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return None

    @staticmethod
    def _extract_timezone_from_u2_page(soup: BeautifulSoup) -> Optional[str]:
        """从 U2 页面提取用户时区（参考 u2_magic.py get_tz）。

        U2 的时间字符串通常是“用户个人设置的时区”下的显示时间。
        直接把该时间当作服务器本地时间会导致发布时间偏移，进而影响
        “新/中/老种”的汇报间隔判断（30/45/60 分钟）。

        返回值应为 IANA 时区名称（如 Asia/Shanghai）。解析失败返回 None。
        """
        try:
            a = soup.find('a', href=re.compile(r'usercp\.php\?action=tracker#timezone'))
            if not a:
                return None
            title = (a.get('title') or '').strip()
            if not title:
                return None

            # 多语言前后缀（与脚本保持一致）
            pre_suf = [
                ('时区', '，点击修改。'),
                ('時區', '，點擊修改。'),
                ('Current timezone is ', ', click to change.'),
            ]
            for pre, suf in pre_suf:
                if title.startswith(pre):
                    tz = title[len(pre):]
                    if suf and tz.endswith(suf):
                        tz = tz[:-len(suf)]
                    return tz.strip() or None
        except Exception:
            return None
        return None

    def _parse_u2_time_to_timestamp(self, date_str: str, tz_name: Optional[str]) -> Optional[float]:
        """解析 U2 页面上的时间字符串为时间戳。

        U2 的 <time> 标签通常在 title 属性里给出完整时间，例如:
        - 2025-01-31 12:34:56
        - 2025-01-31 12:34

        此处做宽松解析并可选绑定时区（来自 _extract_timezone_from_u2_page）。
        """
        try:
            s = (date_str or "").strip()
            if not s:
                return None

            # 压缩空白
            s = re.sub(r"\s+", " ", s)

            # 常见格式
            fmts = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y/%m/%d",
            ]

            publish_dt: Optional[datetime] = None
            for fmt in fmts:
                try:
                    publish_dt = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    continue

            if publish_dt is None:
                # 尝试 ISO 解析（兼容 "YYYY-MM-DDTHH:MM:SS" 等）
                try:
                    publish_dt = datetime.fromisoformat(s)
                except Exception:
                    publish_dt = None

            if publish_dt is None:
                return None

            if tz_name and ZoneInfo is not None and publish_dt.tzinfo is None:
                try:
                    publish_dt = publish_dt.replace(tzinfo=ZoneInfo(tz_name))
                except Exception:
                    # 时区无效则忽略，按本地/naive 处理
                    pass

            return float(publish_dt.timestamp())
        except Exception:
            return None

    def _is_u2_site(self, site_rule: Optional[SpeedLimitSite], tracker_domain: str) -> bool:
        """判断站点规则是否属于 U2（用于启用脚本风格的 30/45/60 分钟间隔）。"""
        if not site_rule:
            return False

        base_url = (self._get_site_base_url(site_rule) or '').lower()
        cookie = (site_rule.peerlist_cookie or '').lower()
        td = (tracker_domain or '').lower()

        if 'u2.dmhy' in base_url:
            return True
        # U2 的 NexusPHP cookie 名通常含 nexusphp_u2
        if 'nexusphp_u2' in cookie:
            return True
        # tracker 域名也通常含 dmhy（如 daydream.dmhy.best）
        if 'dmhy' in td:
            return True

        return False

    async def _ensure_u2_publish_time(self, site_rule: SpeedLimitSite, torrent: TorrentInfo, state: Optional[TorrentState]) -> Optional[float]:
        """确保获取并缓存 U2 的发布时间。

        - 优先使用模块级 _publish_time_cache / state.publish_time
        - 缺失时按 hash 搜索获取（与 u2_magic.py update_tid 一致）

        返回 publish_time（unix timestamp），失败返回 None。
        """
        global _publish_time_cache

        cached = _publish_time_cache.get(torrent.hash)
        if cached and cached > 0:
            if state and not state.publish_time:
                state.publish_time = cached
            return cached

        if state and state.publish_time and state.publish_time > 0:
            _publish_time_cache[torrent.hash] = float(state.publish_time)
            return float(state.publish_time)

        # 没 cookie 无法访问搜索页
        if not site_rule.peerlist_cookie:
            return None

        _tid, publish_time = await self._search_tid_by_hash(site_rule, torrent)
        if publish_time and publish_time > 0:
            _publish_time_cache[torrent.hash] = float(publish_time)
            if state:
                state.publish_time = float(publish_time)
            return float(publish_time)

        return None

    def _get_cached_tid(self, torrent: TorrentInfo) -> Optional[str]:
        """从模块级缓存获取TID（种子TID不会变化，可永久缓存）"""
        global _tid_cache
        if torrent.hash in _tid_cache:
            tid = _tid_cache[torrent.hash]
            logger.debug(f"[{torrent.name[:20] if torrent.name else 'unknown'}] 从缓存获取TID: {tid}")
            return tid
        return None

    async def _search_tid_by_hash(self, site_rule: SpeedLimitSite, torrent: TorrentInfo) -> Tuple[Optional[str], Optional[float]]:
        """通过hash在网站搜索获取TID和发布时间（参考u2_magic.py的update_tid方法）

        注意：此方法会访问PT站点搜索页面，使用TID缓存避免频繁请求
        每个种子的TID只会搜索一次，之后从缓存获取

        Returns:
            (tid, publish_time): TID字符串和发布时间戳，如果获取失败则为None
        """
        if not site_rule.peerlist_cookie:
            return None, None

        base_url = self._get_site_base_url(site_rule)
        if not base_url:
            return None, None

        try:
            # 构建搜索URL - NexusPHP格式 search_area=5 表示按hash搜索
            search_url = f"{base_url}/torrents.php?search={torrent.hash}&search_area=5"

            headers = {"user-agent": "PT-Manager-Pro"}
            cookies = {}
            for item in site_rule.peerlist_cookie.split(";"):
                if "=" in item:
                    key, value = item.split("=", 1)
                    cookies[key.strip()] = value.strip()

            logger.debug(f"[{torrent.name[:20]}] 通过hash搜索TID: {search_url}")

            # 使用共享 HTTP 客户端
            http_client = await get_http_client()
            response = await http_client.get(search_url, headers=headers, cookies=cookies)

            if response.status_code != 200:
                logger.info(f"[{torrent.name[:20]}] hash搜索失败: HTTP {response.status_code}")
                return None, None

            # 解析搜索结果，提取TID和发布时间
            soup = BeautifulSoup(response.text, "lxml")

            # U2 的时间显示可能是“用户个人设置的时区”，需要先取出 tz 才能准确换算成 timestamp
            page_tz = self._extract_timezone_from_u2_page(soup)

            # 检查是否有搜索结果
            # U2 搜索结果在 class="torrents" 的表格中
            torrents_table = soup.find("table", class_="torrents")
            if not torrents_table:
                logger.info(f"[{torrent.name[:20]}] hash搜索未找到种子表格，可能无结果或cookie无效")
                # 记录页面标题帮助调试
                title = soup.find("title")
                if title:
                    logger.info(f"[{torrent.name[:20]}] 页面标题: {title.get_text()}")
                return None, None

            # 在种子表格中查找 details.php 链接和发布时间
            # 因为是按 hash 搜索，通常只有一个结果，但仍按“包含 details.php?id= 的行”定位更稳健
            global _tid_cache, _publish_time_cache
            tid: Optional[str] = None
            publish_time: Optional[float] = None

            # 先在每一行里找 details 链接，锁定对应行（参考 u2_magic.py 的 table[0].contents[1]）
            result_row = None
            for row in torrents_table.find_all("tr"):
                detail_link = row.find("a", href=re.compile(r"details\.php\?id=\d+"))
                if not detail_link:
                    continue
                href = detail_link.get("href", "")
                match = re.search(r"id=(\d+)", href)
                if match:
                    tid = match.group(1)
                    result_row = row
                    logger.debug(f"[{torrent.name[:20]}] 通过hash搜索获取到TID: {tid}")
                    _tid_cache[torrent.hash] = tid
                    break

            # 提取发布时间：
            # 1) 尝试第 4 列（u2_magic.py 使用 contents[3].time）
            # 2) 如果失败，则在该行所有 <time> 中选择“最早且不在未来”的时间（避免误取促销结束时间）
            candidates: list[tuple[float, str]] = []
            if result_row is not None:
                tds = result_row.find_all("td")
                if len(tds) >= 4:
                    tt = tds[3].find("time")
                    if tt:
                        ds = (tt.get("title") or tt.get_text(" ", strip=True) or "").strip()
                        ts = self._parse_u2_time_to_timestamp(ds, page_tz) if ds else None
                        if ts:
                            candidates.append((ts, ds))

                # 收集该行所有 time
                for tt in result_row.find_all("time"):
                    ds = (tt.get("title") or tt.get_text(" ", strip=True) or "").strip()
                    ts = self._parse_u2_time_to_timestamp(ds, page_tz) if ds else None
                    if ts:
                        candidates.append((ts, ds))

            # 兜底：表格里所有 time
            if not candidates:
                for tt in torrents_table.find_all("time"):
                    ds = (tt.get("title") or tt.get_text(" ", strip=True) or "").strip()
                    ts = self._parse_u2_time_to_timestamp(ds, page_tz) if ds else None
                    if ts:
                        candidates.append((ts, ds))

            if candidates:
                now_ts = time.time()
                past = [(ts, ds) for ts, ds in candidates if ts <= now_ts + 60]
                if past:
                    # 选择最早的过去时间作为发布时间（更稳：避免取到“最近活动时间”等）
                    publish_time, date_str = min(past, key=lambda x: x[0])
                    _publish_time_cache[torrent.hash] = publish_time
                    logger.debug(f"[{torrent.name[:20]}] 获取到发布时间: {date_str} ({publish_time})")
                    return tid, publish_time
                else:
                    # 全部在未来，说明抓取到了错误的 time（通常是促销结束时间）或时区异常
                    logger.debug(f"[{torrent.name[:20]}] 时间候选均在未来，忽略发布时间候选: {[d for _, d in candidates][:3]}")
            logger.debug(f"[{torrent.name[:20]}] hash搜索未找到TID")
            return None, None

        except Exception as e:
            logger.debug(f"[{torrent.name[:20]}] hash搜索TID失败: {e}")
            return None, None

    async def _get_peerlist_time_cached(
        self,
        site_rule: SpeedLimitSite,
        torrent_hash: str,
        tid: str,
        now: float
    ) -> Optional[int]:
        """获取peerlist时间（带缓存）

        缓存策略：
        - 缓存有效期内，动态计算当前空闲时间
        - 缓存过期后，重新从站点获取

        Args:
            site_rule: 站点规则
            torrent_hash: 种子hash（用于缓存key）
            tid: 种子ID
            now: 当前时间戳

        Returns:
            空闲时间（秒），如果peerlist_time_mode是elapsed
        """
        global _peerlist_cache

        # 检查缓存
        if torrent_hash in _peerlist_cache:
            cache_time, cached_idle = _peerlist_cache[torrent_hash]
            cache_age = now - cache_time

            if cache_age < PEERLIST_CACHE_TTL:
                # 缓存有效，动态计算当前空闲时间
                if site_rule.peerlist_time_mode == 'remaining':
                    current_idle = max(int(cached_idle - cache_age), 0)
                else:
                    current_idle = int(cached_idle + cache_age)
                logger.debug(f"[peerlist缓存] hash={torrent_hash[:8]}, "
                           f"缓存时间={cache_age:.0f}秒, 空闲时间={current_idle}秒")
                return current_idle

        # 缓存过期或不存在，从站点获取
        peerlist_time = await self._peerlist_get_time(site_rule, tid)

        if peerlist_time is not None:
            # 更新缓存
            _peerlist_cache[torrent_hash] = (now, peerlist_time)
            logger.debug(f"[peerlist更新] hash={torrent_hash[:8]}, 空闲时间={peerlist_time}秒")

        return peerlist_time

    async def _peerlist_get_time(self, site_rule: SpeedLimitSite, tid: str) -> Optional[int]:
        """从peerlist页面获取时间（秒）- 内部方法，请使用 _get_peerlist_time_cached

        返回解析出的时间值，具体含义由 site_rule.peerlist_time_mode 决定：
        - "elapsed": 已过时间（从上次汇报到现在）
        - "remaining": 剩余时间（距离下次汇报）
        """
        if not site_rule.peerlist_cookie:
            logger.info(f"peerlist配置不完整: cookie未设置")
            return None

        base_url = self._get_site_base_url(site_rule)
        if not base_url:
            logger.info(f"peerlist配置不完整: 站点URL未设置")
            return None

        # 自动构建peerlist URL (NexusPHP标准格式)
        url = f"{base_url}/viewpeerlist.php?id={tid}"
        logger.debug(f"peerlist请求URL: {url}")
        headers = {"user-agent": "PT-Manager-Pro"}
        cookies = {}
        for item in site_rule.peerlist_cookie.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()
        logger.debug(f"peerlist cookies数量: {len(cookies)}")
        try:
            # 使用共享 HTTP 客户端
            http_client = await get_http_client()
            response = await http_client.get(url, headers=headers, cookies=cookies)
            logger.debug(f"peerlist响应状态: HTTP {response.status_code}")
            if response.status_code >= 300:
                logger.info(f"peerlist请求失败: HTTP {response.status_code}")
                return None

            html_text = response.text.replace("\n", " ")
            soup = BeautifulSoup(html_text, "lxml")

            # 尝试多种时间格式解析
            rows_found = 0
            for row in soup.find_all("tr"):
                if not row.get("bgcolor"):
                    continue
                rows_found += 1
                row_text = row.get_text(" ")
                logger.debug(f"peerlist解析行: {row_text[:100]}...")

                # 格式1: HH:MM:SS 或 MM:SS (取最后一个时间，即空闲时间)
                all_times = re.findall(r"\b(\d+):(\d+)(?::(\d+))?\b", row_text)
                if all_times:
                    # 取最后一个时间（空闲时间），而不是第一个（做种时间）
                    last_time = all_times[-1]
                    logger.debug(f"peerlist找到{len(all_times)}个时间，取最后一个: {last_time}")
                    # findall返回的是tuple，需要处理可能为空的秒数
                    h_or_m, m_or_s, s = last_time
                    h_or_m = int(h_or_m)
                    m_or_s = int(m_or_s)
                    s = int(s) if s else 0
                    if s == 0 and last_time[2] == '':
                        # MM:SS 格式
                        result = h_or_m * 60 + m_or_s
                    else:
                        # HH:MM:SS 格式
                        result = h_or_m * 3600 + m_or_s * 60 + s
                    logger.debug(f"peerlist解析时间: {result}秒 (格式: HH:MM:SS)")
                    return result

                # 格式2: "X分Y秒" 或 "X分钟Y秒"
                chinese_match = re.search(r"(\d+)\s*分(?:钟)?\s*(\d+)\s*秒", row_text)
                if chinese_match:
                    minutes, seconds = map(int, chinese_match.groups())
                    result = minutes * 60 + seconds
                    logger.debug(f"peerlist解析时间: {result}秒 (格式: X分Y秒)")
                    return result

                # 格式3: "X小时Y分Z秒"
                chinese_full_match = re.search(r"(\d+)\s*小时\s*(\d+)\s*分(?:钟)?\s*(\d+)\s*秒", row_text)
                if chinese_full_match:
                    hours, minutes, seconds = map(int, chinese_full_match.groups())
                    result = hours * 3600 + minutes * 60 + seconds
                    logger.debug(f"peerlist解析时间: {result}秒 (格式: X小时Y分Z秒)")
                    return result

                # 格式4: 纯秒数
                seconds_match = re.search(r"\b(\d+)\s*秒\b", row_text)
                if seconds_match and "分" not in row_text:
                    result = int(seconds_match.group(1))
                    logger.debug(f"peerlist解析时间: {result}秒 (格式: X秒)")
                    return result

            logger.debug(f"peerlist未找到匹配的时间格式 (检查了{rows_found}行)")
        except Exception as e:
            logger.debug(f"获取 peer list 失败: {e}")
        return None

    @staticmethod
    def _normalize_next_announce(
        next_announce: Optional[float],
        announce_interval: Optional[int],
        added_time: Optional[datetime],
        now: float,
    ) -> Optional[float]:
        if not next_announce or next_announce <= 0:
            return None
        if announce_interval and next_announce > announce_interval:
            next_announce = announce_interval
        if announce_interval and added_time:
            added_ts = added_time.timestamp()
            if now - added_ts < announce_interval:
                delta = now - added_ts + next_announce - announce_interval
                if abs(delta) <= 5:
                    return next_announce
                if delta < -600:
                    return None
        return next_announce

    
    def _calculate_limit(
        self,
        state: TorrentState,
        current_speed: float,
        target_speed: float,
        now: float,
        safety_margin: float = 0.0,
        is_downloading: bool = False,
        eta_seconds: int = 0,
    ) -> int:
        """计算上传限速值（按用户提供的 qBit Smart Limit v10.9.1 逻辑）

        - 以“本汇报周期”为单位，尽量让周期平均速度接近目标速度
        - 使用 PID + 卡尔曼预测 + 分阶段策略
        - 返回 0 表示不限速（与 qBittorrent API 一致）
        """

        # 1) 目标速度（考虑安全余量）
        base_target = max(0.0, target_speed * (1 - max(0.0, safety_margin)))
        if base_target <= 0:
            state.phase = C.PHASE_IDLE
            return 0

        # 2) 速度追踪
        filtered_speed, _accel = state.kalman.update(current_speed, now)
        state.tracker_speed.record(now, current_speed)

        # 3) 周期进度追踪（用于可视化/调试）
        state.update_cycle_progress(target_speed, safety_margin)

        # 4) 计算时间与阶段
        time_left = state.get_time_left(now)
        if time_left <= 2 or time_left > 1e4:
            state.phase = C.PHASE_WARMUP if not state.cycle_synced else C.PHASE_IDLE
            return 0

        # 按阶段权重拿更稳的速度估计
        phase_probe = get_phase(time_left, state.cycle_synced, True)
        tracked_speed = state.tracker_speed.get_weighted_avg(now, phase_probe)
        if tracked_speed <= 0:
            tracked_speed = filtered_speed if filtered_speed > 0 else current_speed

        # 5) 目标总量/进度
        elapsed = max(0.0, now - state.cycle_start_time) if state.cycle_start_time > 0 else 0.0
        total_time = max(1.0, elapsed + time_left)

        correction = state.precision_tracker.get_correction() if state.precision_tracker else 1.0
        adjusted_target = max(1.0, base_target * correction)

        target_total = adjusted_target * total_time
        uploaded = max(0.0, state.total_uploaded - state.cycle_start_uploaded)
        progress = uploaded / target_total if target_total > 0 else 0.0

        # 6) 预测/触发（避免过早限速）
        #    predicted_* 用于阶段/完结修正；触发条件采用“预算式”判断（参考 u2_magic.py），
        #    只在接近超标时才开始限速，避免刚开周期就把速度压下去。
        predicted_total = uploaded + state.kalman.predict_upload(time_left)
        predicted_ratio = predicted_total / target_total if target_total > 0 else 1.0

        # 预算式触发：允许前期短时高速，只有当“再放开一小段时间 + 后续保持低速”会超标时，才进入限速
        buffer_seconds = getattr(C, "LIMIT_TRIGGER_BUFFER_SEC", 10.0)
        floor_ratio = getattr(C, "LIMIT_TRIGGER_FLOOR_RATIO", 0.12)
        floor_ratio = max(getattr(C, "LIMIT_TRIGGER_FLOOR_RATIO_MIN", 0.05),
                          min(floor_ratio, getattr(C, "LIMIT_TRIGGER_FLOOR_RATIO_MAX", 0.20)))
        floor_speed = max(0.0, adjusted_target * floor_ratio)

        # 对下载中任务：完成可能触发汇报（脚本里有 ETA+10s 的余量），这里保持一致
        effective_tl = time_left
        if is_downloading and eta_seconds is not None and eta_seconds > 0:
            effective_tl = min(time_left, float(eta_seconds) + 10.0)

        buffer_speed = max(float(current_speed), float(tracked_speed))
        soft_predicted_total = uploaded + buffer_speed * buffer_seconds + floor_speed * max(0.0, effective_tl)

        # 还没接近超标：不必提前限速
        if soft_predicted_total <= target_total and progress < 1.0:
            state.phase = C.PHASE_IDLE
            return 0

        needs_limiting = (soft_predicted_total > target_total) or (progress >= 1.0)

        phase = get_phase(time_left, state.cycle_synced, needs_limiting)
        state.phase = phase
        if phase == C.PHASE_IDLE:
            return 0

        # 7) 需要达到的速度
        need = target_total - uploaded
        if need <= 0:
            limit = C.MIN_LIMIT
        else:
            required_speed = need / max(time_left, 1.0)

            # PID 控制输出（比例因子）
            state.pid.set_phase(phase)
            pid_output = state.pid.update(target_total, uploaded, now)

            # 分阶段策略（与脚本一致）
            if phase == C.PHASE_FINISH:
                # Finish: 更严格地校正，避免临近汇报时超/欠速
                correction_factor = 1.0
                if predicted_ratio > 1.002:
                    correction_factor = 1 - (predicted_ratio - 1) * 3
                    correction_factor = max(0.8, correction_factor)
                elif predicted_ratio < 0.998:
                    correction_factor = 1 + (1 - predicted_ratio) * 3
                    correction_factor = min(1.2, correction_factor)
                limit = required_speed * pid_output * correction_factor

            elif phase == C.PHASE_STEADY:
                headroom = C.PID_PARAMS.get(phase, {}).get('headroom', 1.0)
                if predicted_ratio > 1.01:
                    headroom = 1.0
                elif predicted_ratio < 0.95:
                    headroom = 1.03
                limit = required_speed * headroom * pid_output

            elif phase == C.PHASE_CATCH:
                if required_speed > adjusted_target * 5:
                    # 追赶阶段太落后，直接放开
                    return 0
                headroom = C.PID_PARAMS.get(phase, {}).get('headroom', 1.0)
                limit = required_speed * headroom * pid_output

            else:  # warmup
                # 预热阶段：达到一定进度后开始“温控/精控”
                if progress >= 1.0:
                    limit = C.MIN_LIMIT
                elif progress >= 0.8:
                    limit = required_speed * 1.01 * pid_output
                elif progress >= 0.5:
                    limit = required_speed * 1.05
                else:
                    return 0

            limit = max(C.MIN_LIMIT, limit)

        # 8) 量化（减少抖动）
        trend = state.tracker_speed.get_recent_trend(now)
        limit = AdaptiveQuantizer.quantize(int(limit), phase, tracked_speed, adjusted_target, trend)

        # 9) 保护：进度接近完成时，防止大爆发
        if progress >= C.PROGRESS_PROTECT and current_speed > adjusted_target * C.SPEED_PROTECT_RATIO:
            protect = int(adjusted_target * C.SPEED_PROTECT_LIMIT)
            if limit == 0 or limit > protect:
                limit = protect

        return max(0, int(limit))


    async def apply_limits(self) -> Dict[str, Any]:
        """应用限速 - 使用上下文管理器确保连接正确释放"""
        config = await self.get_config()
        if not config or not config.enabled:
            return {"enabled": False}

        site_rules = await self.get_site_rules()
        site_rule_map = {r.tracker_domain: r for r in site_rules}

        # 获取所有启用的下载器
        result = await self.db.execute(
            select(Downloader).where(Downloader.enabled == True)
        )
        downloaders = result.scalars().all()
        auto_downloaders = [dl for dl in downloaders if dl.auto_speed_limit]
        if auto_downloaders:
            downloaders = auto_downloaders

        results = {}
        now = time.time()

        # 定期清理缓存，防止内存泄漏
        cleanup_caches()

        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if not client:
                        continue

                    torrents = await client.get_torrents()

                    for torrent in torrents:
                        if torrent.status not in ['seeding', 'downloading']:
                            continue

                        tracker = await self._resolve_tracker_domain(client, torrent)
                        if not tracker:
                            continue

                        # 获取目标速度和安全余量
                        site_rule = site_rule_map.get(tracker)
                        if site_rule:
                            target_speed = site_rule.target_upload_speed
                            safety_margin = site_rule.safety_margin
                            limit_download = getattr(site_rule, 'limit_download_speed', False)
                            optimize_announce = getattr(site_rule, 'optimize_announce', False)
                        else:
                            target_speed = config.target_upload_speed
                            safety_margin = config.safety_margin
                            limit_download = False
                            optimize_announce = False

                        # 获取或创建状态（在 target_speed 检查前，确保统计数据始终被记录）
                        state = self._get_or_create_state(torrent, tracker)

                        # 即使不限速也记录上传/下载增量统计
                        if target_speed <= 0:
                            if state.last_record_uploaded == 0 and torrent.uploaded > 0:
                                state.last_record_uploaded = torrent.uploaded
                            if state.last_record_downloaded == 0 and torrent.downloaded > 0:
                                state.last_record_downloaded = torrent.downloaded
                            delta_up = max(0, torrent.uploaded - state.last_record_uploaded)
                            delta_dl = max(0, torrent.downloaded - state.last_record_downloaded)
                            state.last_record_uploaded = torrent.uploaded
                            state.last_record_downloaded = torrent.downloaded
                            if delta_up > 0 or delta_dl > 0:
                                record = SpeedLimitRecord(
                                    tracker_domain=tracker,
                                    downloader_id=downloader.id,
                                    current_speed=torrent.upload_speed,
                                    target_speed=0,
                                    limit_applied=0,
                                    phase="disabled",
                                    uploaded=delta_up,
                                    downloaded=delta_dl,
                                )
                                self.db.add(record)
                            continue

                        # 更新下载相关状态（用于下载限速和汇报优化）
                        state.total_done = getattr(torrent, 'completed', 0) or torrent.downloaded
                        state.total_size_torrent = torrent.size
                        state.download_speed = torrent.download_speed
                        # 计算 ETA
                        remaining = state.total_size_torrent - state.total_done
                        if torrent.download_speed > 0 and remaining > 0:
                            state.eta = int(remaining / torrent.download_speed)
                        else:
                            state.eta = 0

                        # 记录详细进度（用于汇报优化）
                        if optimize_announce or limit_download:
                            state.detail_progress.append((torrent.uploaded, state.total_done, now))

                        # 获取汇报时间信息 - 关键链路
                        # 始终尝试从 qBittorrent 获取最新的 reannounce 数据
                        next_announce = torrent.next_announce_time
                        announce_interval = torrent.announce_interval
                        fetch_attempted = False

                        # 总是尝试获取最新数据（不仅仅是当 None 时）
                        try:
                            tracker_next, tracker_interval = await client.get_torrent_announce_info(torrent.hash)
                            fetch_attempted = True

                            # 如果获取到有效的 next_announce，使用它
                            if tracker_next and tracker_next > now:
                                next_announce = tracker_next
                                remaining = int(tracker_next - now)
                                logger.debug(f"[{torrent.name[:20]}] 获取 next_announce: {remaining}秒后")

                            # 如果获取到有效的 interval，使用它
                            if tracker_interval and tracker_interval > 0:
                                announce_interval = tracker_interval

                        except Exception as e:
                            logger.debug(f"获取 tracker 信息失败: {e}")

                        # 如果仍然没有 next_announce，使用已保存状态或估算
                        if next_announce is None and state.next_announce_time and state.next_announce_time > now:
                            next_announce = state.next_announce_time
                            logger.debug(f"[{torrent.name[:20]}] 使用已保存的 next_announce: {int(next_announce - now)}秒后")


                        # === 汇报周期：U2 老种并非固定 30 分钟（严格按 u2_magic.py：新30/中45/老60）===
                        # 说明：
                        # - qB trackers/properties 不一定提供真实 interval；如果直接用 added_time 估算，会把“刚下载的老种”当新种。
                        # - u2_magic.py 通过网页发布时间 delta 判定汇报周期，因此这里必须优先拿 publish_time。
                        interval_hint = announce_interval
                        cycle_interval = 0

                        # 1) 站点自定义间隔优先
                        if site_rule and getattr(site_rule, 'custom_announce_interval', 0) > 0:
                            cycle_interval = int(site_rule.custom_announce_interval)

                        # 2) U2 站点：按发布时间估算 30/45/60 分钟（与脚本一致）
                        elif site_rule and self._is_u2_site(site_rule, tracker):
                            publish_time = await self._ensure_u2_publish_time(site_rule, torrent, state)
                            added_ts = torrent.added_time.timestamp() if torrent.added_time else now
                            min_interval = 300
                            if interval_hint and interval_hint > 0:
                                try:
                                    min_interval = max(min_interval, int(interval_hint))
                                except Exception:
                                    pass

                            if publish_time and publish_time > 0:
                                cycle_interval = int(
                                    estimate_announce_interval(
                                        publish_time,
                                        min_interval=min_interval,
                                        seeding_time=torrent.seeding_time or 0,
                                        is_publish_time=True,
                                    )
                                )
                            else:
                                cycle_interval = int(
                                    estimate_announce_interval(
                                        added_ts,
                                        min_interval=min_interval,
                                        seeding_time=torrent.seeding_time or 0,
                                        is_publish_time=False,
                                    )
                                )

                            # 还没通过跳变采样“真实同步”时，允许用估算值覆盖旧版本的错误 1800s
                            have_measured = len(state.interval_samples) >= 2
                            if not have_measured:
                                if (not state.cycle_synced) or (state.cycle_interval <= 0) or (abs(state.cycle_interval - cycle_interval) > 60):
                                    state.cycle_interval = float(cycle_interval)
                                    state.cycle_synced = True
                            # 无论如何都记录当前 announce_interval（用于 UI/debug）
                            if cycle_interval > 0:
                                state.announce_interval = int(cycle_interval)

                        # 3) 其他站点：优先用客户端 interval，否则回退状态估算
                        else:
                            try:
                                if interval_hint and interval_hint > 0:
                                    cycle_interval = int(interval_hint)
                                else:
                                    cycle_interval = int(state.get_announce_interval())
                            except Exception:
                                cycle_interval = int(state.get_announce_interval())

                            if cycle_interval > 0 and ((not state.cycle_synced) or state.cycle_interval <= 0):
                                state.cycle_interval = float(cycle_interval)
                                state.cycle_synced = True


                        # === u2_magic(脚本)风格：next_announce 可靠性检测 + peerlist 兜底 ===
                        ana_state = self._ana_state.setdefault(getattr(downloader, "id", 0) or 0, {"ana": None, "updated": False})
                        # 统一为 int 秒
                        try:
                            cycle_interval = int(cycle_interval) if cycle_interval else 0
                        except Exception:
                            cycle_interval = 0

                        next_remaining = None
                        if next_announce and next_announce > now:
                            next_remaining = float(next_announce - now)

                        
                        # === u2_magic 风格增强：next_announce 跳变检测（比脚本更稳）===
                        # 期望 next_remaining 随时间线性减少；若出现异常跳变，说明客户端 next_announce 可能不可信。
                        if next_remaining is not None and cycle_interval:
                            if state.last_next_remaining is not None and state.last_next_update_time > 0:
                                expected = state.last_next_remaining - (now - state.last_next_update_time)

                                # 允许跨周期 wrap：把 expected 拉回到合理区间再比较
                                if expected < 0:
                                    expected = expected % cycle_interval
                                if expected > cycle_interval:
                                    expected = expected % cycle_interval

                                diff = next_remaining - expected

                                # 强制汇报(900s)可能导致 diff 近似 ±900，视为正常偏差（不下结论）
                                forced_like = (abs(diff - self._FORCED_REANNOUNCE_INTERVAL) < 10) or (abs(diff + self._FORCED_REANNOUNCE_INTERVAL) < 10)

                                # 大跳变阈值：至少 120s，且至少占周期 15%
                                jump_threshold = max(120.0, cycle_interval * 0.15)

                                if (not forced_like) and abs(diff) > jump_threshold:
                                    state.next_jump_suspect_count += 1
                                    logger.debug(
                                        f"[{torrent.name[:20]}] next_announce 跳变: diff={diff:.0f}s, "
                                        f"expected~{expected:.0f}s, now={next_remaining:.0f}s, "
                                        f"suspect={state.next_jump_suspect_count}"
                                    )
                                else:
                                    # 逐步衰减怀疑计数，避免偶发抖动导致误判
                                    state.next_jump_suspect_count = max(0, state.next_jump_suspect_count - 1)

                                # 连续多次跳变：直接判定不可信（除非刚强制汇报/刚手动 reannounce）
                                if state.next_jump_suspect_count >= 2 and ana_state.get("ana") is not False:
                                    recent_ra = (now - state.last_reannounce) < 120 or (now - state.last_force_reannounce) < 120
                                    if not recent_ra:
                                        ana_state["ana"] = False
                                        ana_state["updated"] = True
                                        logger.info(f"[{torrent.name[:20]}] next_announce 多次跳变，判定不可信，后续使用 peerlist 推断")

                            # 更新观测值
                            state.last_next_remaining = float(next_remaining)
                            state.last_next_update_time = now

# 观察期：利用 added_time 校验 next_announce 是否与一个完整周期对齐
                        if (not ana_state.get("updated")) and next_remaining is not None and torrent.added_time and cycle_interval:
                            added_ts = torrent.added_time.timestamp()
                            if now - added_ts < cycle_interval:
                                delta = (now - added_ts) + next_remaining - cycle_interval
                                if abs(delta) <= 5:
                                    ana_state["ana"] = True
                                    ana_state["updated"] = True
                                    logger.debug(f"[{torrent.name[:20]}] next_announce 校验通过，判定可信")
                                elif delta < -600:
                                    # next_announce 疑似异常：用 peerlist idle 反推 last_announce_time 再判断
                                    if (not state.last_announce_time) and (not state.next_announce_is_true) and site_rule and site_rule.peerlist_enabled:
                                        tid = self._get_cached_tid(torrent)
                                        publish_time = _publish_time_cache.get(torrent.hash)
                                        if not tid:
                                            tid, publish_time = await self._search_tid_by_hash(site_rule, torrent)
                                        if publish_time and state and not state.publish_time:
                                            state.publish_time = publish_time
                                        if tid:
                                            peer_t = await self._get_peerlist_time_cached(site_rule, torrent.hash, tid, now)
                                            if peer_t is not None:
                                                time_mode = getattr(site_rule, 'peerlist_time_mode', 'elapsed')
                                                if time_mode == "remaining":
                                                    last_announce = now + peer_t - cycle_interval
                                                else:
                                                    last_announce = now - peer_t
                                                # 强制汇报识别（u2_magic 脚本逻辑）：若 last_announce + 900 ≈ now + next_remaining，则还不能下结论
                                                if abs((last_announce + self._FORCED_REANNOUNCE_INTERVAL) - now - next_remaining) < 5:
                                                    state.next_announce_is_true = True
                                                    state.last_announce_time = None
                                                    logger.debug(f"[{torrent.name[:20]}] 疑似强制汇报引起偏差，继续观察")
                                                else:
                                                    ana_state["ana"] = False
                                                    ana_state["updated"] = True
                                                    logger.info(f"[{torrent.name[:20]}] next_announce 判定不可信，后续使用 peerlist 推断")

                        # 若 next_announce 不可信：优先用 peerlist idle 推断 last_announce_time / next_announce
                        if ana_state.get("ana") is False and site_rule and site_rule.peerlist_enabled and cycle_interval:
                            if not state.last_announce_time:
                                tid = self._get_cached_tid(torrent)
                                publish_time = _publish_time_cache.get(torrent.hash)
                                if not tid:
                                    tid, publish_time = await self._search_tid_by_hash(site_rule, torrent)
                                if publish_time and state and not state.publish_time:
                                    state.publish_time = publish_time
                                if tid:
                                    peer_t = await self._get_peerlist_time_cached(site_rule, torrent.hash, tid, now)
                                    if peer_t is not None:
                                        time_mode = getattr(site_rule, 'peerlist_time_mode', 'elapsed')
                                        if time_mode == "remaining":
                                            state.last_announce_time = now + peer_t - cycle_interval
                                        else:
                                            state.last_announce_time = now - peer_t
                            if state.last_announce_time:
                                next_announce = state.last_announce_time + cycle_interval
                                logger.debug(f"[{torrent.name[:20]}] 使用 peerlist 推断 next_announce: {int(next_announce-now)}秒后")

                        # 同步周期 - 传递汇报信息（确保链路完整）
                        state.sync_cycle(
                            torrent.uploaded,
                            now,
                            next_announce=next_announce,
                            # 使用修正后的 cycle_interval（U2: 30/45/60min），不要直接用客户端可能缺失/错误的 interval
                            interval=cycle_interval
                        )

                        # 验证链路：如果 sync_cycle 后 next_announce_time 仍为 None，记录警告
                        if state.next_announce_time is None and fetch_attempted:
                            logger.debug(f"[{torrent.name[:20]}] 警告: 无法获取有效的 next_announce_time")

                        # 计算限速 - 传递安全余量
                        raw_limit = self._calculate_limit(state, torrent.upload_speed, target_speed, now, safety_margin, is_downloading=(torrent.status == 'downloading'), eta_seconds=state.eta)

                        # 应用平滑限速 - 防止限速值剧烈波动
                        if raw_limit > 0:
                            limit = state.smooth_limiter.smooth(raw_limit, torrent.upload_speed, state.phase, now)
                        else:
                            limit = raw_limit
                            state.smooth_limiter.reset()  # 无限速时重置

                        # 检查强制汇报
                        if config.enabled:
                            should_ra, reason = ReannounceOptimizer.should_reannounce(
                                state, torrent.uploaded, torrent.downloaded,
                                target_speed, now
                            )
                            if should_ra:
                                try:
                                    await client.reannounce_torrent(torrent.hash)
                                    state.last_reannounce = now
                                    state.reannounced_this_cycle = True
                                    state.last_announce_time = now
                                    logger.info(f"[{torrent.name[:20]}] 强制汇报: {reason}")
                                except Exception as e:
                                    logger.debug(f"强制汇报失败: {e}")

                        # 应用限速
                        if limit != state.current_limit:
                            try:
                                await client.set_torrent_upload_limit(torrent.hash, limit)
                                old_limit = state.current_limit
                                state.current_limit = limit
                                # 记录限速变更
                                if limit > 0 and old_limit == 0:
                                    logger.info(f"[{torrent.name[:20]}] 开始限速: {limit/1024:.1f}KB/s, 阶段={state.phase}, 速度={torrent.upload_speed/1024:.1f}KB/s")
                                elif limit == 0 and old_limit > 0:
                                    logger.info(f"[{torrent.name[:20]}] 解除限速")
                                elif abs(limit - old_limit) > 10240:  # 变化超过10KB/s才记录
                                    logger.debug(f"[{torrent.name[:20]}] 限速调整: {old_limit/1024:.1f} -> {limit/1024:.1f}KB/s")
                            except Exception as e:
                                logger.error(f"设置限速失败: {e}")

                        # ===== 下载限速功能（参考 u2_magic.py limit_download_speed）=====
                        download_limit_applied = None
                        if limit_download and torrent.status == 'downloading':
                            # 按照 u2_magic.py: this_time = announce_interval - next_announce - 1
                            this_time = state.get_this_time(now)
                            this_up = torrent.uploaded - state.cycle_start_uploaded

                            if this_time > 0 and this_up > 0:
                                dl_limit, dl_reason = DownloadSpeedLimiter.calculate_download_limit(
                                    state=state,
                                    this_time=this_time,
                                    this_up=this_up,
                                    total_size=state.total_size_torrent,
                                    total_done=state.total_done,
                                    eta=state.eta,
                                    current_download_limit=state.current_download_limit,
                                    current_download_speed=torrent.download_speed,
                                    min_time=120
                                )

                                if dl_limit is not None:
                                    try:
                                        if dl_limit == -1:
                                            # 解除下载限速
                                            await client.set_torrent_download_limit(torrent.hash, 0)
                                            state.current_download_limit = -1
                                            logger.info(f"[{torrent.name[:20]}] {dl_reason}")
                                        else:
                                            # 设置下载限速（转换为 bytes/s）
                                            await client.set_torrent_download_limit(torrent.hash, dl_limit * 1024)
                                            state.current_download_limit = dl_limit
                                            logger.info(f"[{torrent.name[:20]}] {dl_reason}")
                                        download_limit_applied = dl_limit
                                    except Exception as e:
                                        logger.error(f"设置下载限速失败: {e}")

                        # ===== 汇报优化功能（参考 u2_magic.py optimize_announce_time）=====
                        optimize_action = None
                        if optimize_announce and torrent.status == 'downloading':
                            # 按照 u2_magic.py: this_time = announce_interval - next_announce - 1
                            this_time = state.get_this_time(now)
                            this_up = torrent.uploaded - state.cycle_start_uploaded
                            announce_interval = state.get_announce_interval()

                            should_act, opt_limit, opt_reason = AnnounceOptimizer.should_optimize(
                                state=state,
                                this_time=this_time,
                                this_up=this_up,
                                announce_interval=announce_interval,
                                now=now
                            )

                            if should_act:
                                try:
                                    if opt_limit is not None:
                                        # 设置等待汇报的限速
                                        await client.set_torrent_upload_limit(torrent.hash, opt_limit * 1024)
                                        state.waiting_for_reannounce = True
                                        state.current_upload_limit = opt_limit
                                        logger.info(f"[{torrent.name[:20]}] 汇报优化: {opt_reason}")
                                        optimize_action = f"等待汇报 (限速{opt_limit}KB/s)"
                                    else:
                                        # 执行强制汇报
                                        if now - state.last_force_reannounce >= C.REANNOUNCE_MIN_INTERVAL:
                                            await client.reannounce_torrent(torrent.hash)
                                            state.last_force_reannounce = now
                                            state.waiting_for_reannounce = False
                                            # 解除等待限速
                                            await client.set_torrent_upload_limit(torrent.hash, 0)
                                            state.current_upload_limit = -1
                                            logger.info(f"[{torrent.name[:20]}] 汇报优化: {opt_reason}")
                                            optimize_action = "强制汇报"
                                except Exception as e:
                                    logger.error(f"汇报优化失败: {e}")

                        # 记录结果
                        results[torrent.hash] = {
                            "name": torrent.name[:30],
                            "tracker": tracker,
                            "current_speed": torrent.upload_speed,
                            "target_speed": target_speed,
                            "limit": limit,
                            "phase": state.phase,
                            "time_left": state.get_time_left(now),
                            "cycle_synced": state.cycle_synced,
                            "cycle_interval": state.cycle_interval or state.get_announce_interval(),
                            "announce_interval": state.get_announce_interval(),
                            # 新增周期进度信息
                            "cycle_progress": state.cycle_progress,
                            "cycle_time_progress": state.cycle_time_progress,
                            "cycle_current_upload": state.cycle_current_upload,
                            "cycle_target_upload": state.cycle_target_upload,
                            "cycle_avg_speed": state.cycle_avg_speed,
                            "estimated_completion": state.estimated_completion,
                            "safety_margin": safety_margin,
                            # 添加 next_announce_time 用于调试
                            "next_announce_time": state.next_announce_time,
                            # 下载限速和汇报优化信息
                            "download_limit": download_limit_applied,
                            "optimize_action": optimize_action,
                            "limit_download_enabled": limit_download,
                            "optimize_announce_enabled": optimize_announce,
                            # 下载状态
                            "total_done": state.total_done,
                            "download_speed": torrent.download_speed,
                            "eta": state.eta,
                        }

                        # 记录到数据库（补全 uploaded/downloaded，用于“今日上传/今日下载”统计）
                        # 计算本轮增量，避免累计值重复相加
                        if state.last_record_uploaded == 0 and torrent.uploaded > 0:
                            # 兼容旧状态文件：第一次不计入 delta，避免瞬时暴涨
                            state.last_record_uploaded = torrent.uploaded
                        if state.last_record_downloaded == 0 and torrent.downloaded > 0:
                            state.last_record_downloaded = torrent.downloaded

                        delta_uploaded = max(0, torrent.uploaded - state.last_record_uploaded)
                        delta_downloaded = max(0, torrent.downloaded - state.last_record_downloaded)
                        state.last_record_uploaded = torrent.uploaded
                        state.last_record_downloaded = torrent.downloaded
                        # 避免写入大量 0 增量记录（不影响今日上传/下载统计）
                        if delta_uploaded == 0 and delta_downloaded == 0:
                            continue

                        record = SpeedLimitRecord(
                            tracker_domain=tracker,
                            downloader_id=downloader.id,
                            current_speed=torrent.upload_speed,
                            target_speed=target_speed,
                            limit_applied=state.current_limit,
                            phase=state.phase,
                            uploaded=delta_uploaded,
                            downloaded=delta_downloaded,
                        )
                        self.db.add(record)

            except Exception as e:
                logger.error(f"处理下载器 {downloader.name} 失败: {e}")

        # 定期保存状态（与本轮记录同一事务提交，避免每次两次 commit）
        await self.save_state(commit=False)
        await self.db.commit()

        return {
            "enabled": True,
            "torrents": results,
            "count": len(results),
        }

    async def clear_limits(self):
        """清除所有限速 - 使用上下文管理器确保连接正确释放"""
        result = await self.db.execute(
            select(Downloader).where(Downloader.enabled == True)
        )
        downloaders = result.scalars().all()

        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if client:
                        torrents = await client.get_torrents()
                        for torrent in torrents:
                            await client.set_torrent_upload_limit(torrent.hash, 0)
            except Exception as e:
                logger.error(f"清除限速失败: {e}")

        # 重置状态
        self.states.clear()
        await self.save_state()
        logger.info("所有限速已清除")

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        now = time.time()
        status = {}

        for hash, state in self.states.items():
            # 动态计算阶段
            time_left = state.get_time_left(now)
            if state.phase != C.PHASE_IDLE:
                display_phase = state.phase
            else:
                display_phase = get_phase(time_left, state.cycle_synced, True)

            status[hash] = {
                "name": state.name,
                "tracker": state.tracker,
                "phase": display_phase,
                "limit": state.current_limit,
                "last_limit": state.current_limit,
                "time_left": time_left,
                "cycle_synced": state.cycle_synced,
                "cycle_interval": state.cycle_interval or state.get_announce_interval(),
                "announce_interval": state.get_announce_interval(),
                "filtered_speed": state.kalman.speed,
                # 周期进度信息
                "cycle_progress": state.cycle_progress,
                "cycle_time_progress": state.cycle_time_progress,
                "cycle_current_upload": state.cycle_current_upload,
                "cycle_target_upload": state.cycle_target_upload,
                "cycle_avg_speed": state.cycle_avg_speed,
                "estimated_completion": state.estimated_completion,
                # 调试信息
                "next_announce_time": state.next_announce_time,
            }

        return status

    async def get_cached_status(self) -> Dict[str, Any]:
        """获取缓存的状态（快速响应），如果缓存过期则刷新"""
        global _status_cache, _status_cache_time
        now = time.time()

        # 使用锁保护缓存访问，防止竞态条件
        async with _cache_lock:
            cache_age = now - _status_cache_time if _status_cache_time > 0 else float('inf')

            # 如果缓存有效，直接返回（更新time_left）
            if _status_cache and cache_age < STATUS_CACHE_TTL:
                # 动态更新time_left（不重新获取数据）
                return self._update_cache_time_left(_status_cache, cache_age)

        # 缓存过期，同步刷新
        return await self.refresh_status()

    def _update_cache_time_left(self, cache: Dict[str, Any], elapsed: float) -> Dict[str, Any]:
        """更新缓存中的time_left字段"""
        updated_cache = {}
        for hash, data in cache.items():
            updated_data = data.copy()
            # 根据缓存时间差更新 time_left（注意: time_left=0 也是有效值，不能用 truthy 判断）
            if 'time_left' in updated_data and updated_data['time_left'] is not None:
                try:
                    tl_val = float(updated_data['time_left'])
                except (TypeError, ValueError):
                    tl_val = 0.0
                tl_val = max(0.0, tl_val - float(elapsed))
                updated_data['time_left'] = tl_val

                # 同时更新 phase
                cycle_synced = updated_data.get('cycle_synced', False)
                if updated_data.get('phase') != C.PHASE_IDLE:
                    updated_data['phase'] = get_phase(tl_val, cycle_synced, True)
            updated_cache[hash] = updated_data
        return updated_cache

    async def refresh_status(self) -> Dict[str, Any]:
        """刷新并获取当前状态 - 优化版本

        优化策略:
        1. 使用 get_torrents(with_reannounce=True) 批量获取的数据
        2. 减少不必要的 API 调用（properties/trackers）
        3. 缓存 comment URL，只在需要时获取
        4. 并行处理多个种子的 peerlist 请求
        """
        now = time.time()
        status = {}
        site_rules = await self.get_site_rules()
        site_rule_map = {r.tracker_domain: r for r in site_rules}

        # 获取所有启用的下载器
        result = await self.db.execute(
            select(Downloader).where(Downloader.enabled == True)
        )
        downloaders = result.scalars().all()

        # 遍历下载器获取实时数据
        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if not client:
                        continue

                    # get_torrents(with_reannounce=True) 已经批量获取了 reannounce 和 next_announce 数据
                    torrents = await client.get_torrents()

                    # 过滤活跃种子
                    active_torrents = [t for t in torrents if t.status in ['seeding', 'downloading']]

                    # 预处理：确定哪些种子需要获取 comment URL (用于peerlist TID提取)
                    torrents_need_comment = []
                    for torrent in active_torrents:
                        tracker = await self._resolve_tracker_domain(client, torrent)
                        if not tracker:
                            continue
                        site_rule = site_rule_map.get(tracker)
                        # 只有启用了 peerlist 且 TID 未缓存时才需要 comment
                        if site_rule and site_rule.peerlist_enabled:
                            if torrent.hash not in _tid_cache and torrent.hash not in _comment_cache:
                                torrents_need_comment.append(torrent)

                    # 批量获取 comment URL（并行请求）
                    if torrents_need_comment and hasattr(client, '_request'):
                        await self._batch_fetch_comments(client, torrents_need_comment)

                    # 处理每个种子
                    for torrent in active_torrents:
                        status_entry = await self._process_torrent_status(
                            client, torrent, site_rule_map, now
                        )
                        if status_entry:
                            status[torrent.hash] = status_entry

            except Exception as e:
                logger.error(f"刷新下载器 {downloader.name} 状态失败: {e}")

        # 使用锁保护缓存更新
        global _status_cache, _status_cache_time
        async with _cache_lock:
            _status_cache = status
            _status_cache_time = now

        return status

    async def _batch_fetch_comments(self, client, torrents: List[TorrentInfo]):
        """批量获取种子的 comment URL"""
        global _comment_cache

        # 使用信号量限制并发，避免一次性对 WebUI 发起过多 properties 请求
        sem = asyncio.Semaphore(10)

        async def fetch_one(torrent: TorrentInfo):
            async with sem:
                try:
                    response = await client._request(
                        "GET",
                        "/api/v2/torrents/properties",
                        params={"hash": torrent.hash},
                        retries=1
                    )
                    if response:
                        props = response.json()
                        comment = props.get("comment", "") or ""
                        if comment:
                            _comment_cache[torrent.hash] = comment
                except Exception:
                    pass

        tasks = [fetch_one(t) for t in torrents]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_torrent_status(
        self,
        client,
        torrent: TorrentInfo,
        site_rule_map: Dict[str, Any],
        now: float
    ) -> Optional[Dict[str, Any]]:
        """处理单个种子的状态"""
        tracker = await self._resolve_tracker_domain(client, torrent)
        if not tracker:
            return None

        # 使用 get_torrents 已经获取的 next_announce_time
        reannounce_seconds = None
        fetch_source = None
        tracker_urls: List[str] = []

        # 优先使用 torrent.next_announce_time（由 get_torrents 批量获取）
        if torrent.next_announce_time and torrent.next_announce_time > now:
            reannounce_seconds = int(torrent.next_announce_time - now)
            fetch_source = "torrent_info"

        # 获取已保存的状态
        state = self.states.get(torrent.hash)

        # 站点规则
        site_rule = site_rule_map.get(tracker)

        # U2 老种的汇报周期不是固定 30 分钟：需要发布时间才能正确判断（30/45/60min）
        publish_time = _publish_time_cache.get(torrent.hash) or (state.publish_time if state else None)
        if site_rule and self._is_u2_site(site_rule, tracker) and (not publish_time or publish_time <= 0):
            publish_time = await self._ensure_u2_publish_time(site_rule, torrent, state)

        # 确定汇报间隔
        interval_source = "unknown"

        # 1) 站点自定义间隔优先
        if site_rule and getattr(site_rule, 'custom_announce_interval', 0) > 0:
            cycle_interval = int(site_rule.custom_announce_interval)
            interval_source = "custom"

        # 2) U2：按发布时间估算 30/45/60min（严格与 u2_magic.py 一致）
        elif site_rule and self._is_u2_site(site_rule, tracker):
            if publish_time and publish_time > 0:
                cycle_interval = int(
                    estimate_announce_interval(
                        publish_time,
                        seeding_time=torrent.seeding_time or 0,
                        is_publish_time=True,
                    )
                )
                interval_source = "estimated_publish"
            elif torrent.seeding_time and torrent.seeding_time > 0:
                added_ts = torrent.added_time.timestamp() if torrent.added_time else now
                cycle_interval = int(
                    estimate_announce_interval(
                        added_ts,
                        seeding_time=torrent.seeding_time or 0,
                        is_publish_time=False,
                    )
                )
                interval_source = "estimated_seeding"
            else:
                added_ts = torrent.added_time.timestamp() if torrent.added_time else now
                cycle_interval = int(estimate_announce_interval(added_ts))
                interval_source = "estimated_added"

            # 若还没通过跳变采样同步真实周期，则用估算值纠正旧版本错误的 1800s
            if state:
                have_measured = (len(state.interval_samples) >= 2) and (state.cycle_interval and state.cycle_interval > 0)

                # 有足够的跳变采样时，以“真实同步周期”为准
                if have_measured:
                    cycle_interval = int(state.cycle_interval)
                    interval_source = "synced"
                else:
                    # 没有真实采样时，用发布时间估算值纠正旧版本错误的 1800s
                    if (not state.cycle_synced) or (state.cycle_interval <= 0) or (abs(state.cycle_interval - cycle_interval) > 60):
                        state.cycle_interval = float(cycle_interval)
                        state.cycle_synced = True

                # 保留脚本含义：announce_interval 代表“应当使用的周期”
                state.announce_interval = int(cycle_interval)

        # 3) 其他站点：优先用已同步周期，否则按时间估算
        else:
            if state and state.cycle_interval > 0:
                cycle_interval = int(state.cycle_interval)
                interval_source = "synced"
            else:
                # 优先使用发布时间，其次做种时间，最后添加时间
                if publish_time and publish_time > 0:
                    cycle_interval = int(estimate_announce_interval(publish_time, seeding_time=torrent.seeding_time, is_publish_time=True))
                    interval_source = "estimated_publish"
                elif torrent.seeding_time and torrent.seeding_time > 0:
                    added_ts = torrent.added_time.timestamp() if torrent.added_time else now
                    cycle_interval = int(estimate_announce_interval(added_ts, seeding_time=torrent.seeding_time, is_publish_time=False))
                    interval_source = "estimated_seeding"
                else:
                    added_ts = torrent.added_time.timestamp() if torrent.added_time else now
                    cycle_interval = int(estimate_announce_interval(added_ts))
                    interval_source = "estimated_added"

        reannounce_seconds = self._normalize_next_announce(
            reannounce_seconds,
            cycle_interval,
            torrent.added_time,
            now,
        )
        # next_announce 倒计时在部分客户端版本会出现“跳变/乱跳”，导致前端显示不准
        # 这里做一次轻量的跳变检测：若连续检测到异常跳变，则优先使用上一轮倒计时推算的值，保证倒计时单调
        if state and reannounce_seconds is not None and cycle_interval and reannounce_seconds > 0:
            try:
                observed_next = float(reannounce_seconds)

                if state.last_next_remaining is not None and state.last_next_update_time > 0:
                    dt_obs = now - float(state.last_next_update_time)
                    expected_raw = float(state.last_next_remaining) - dt_obs
                    expected = expected_raw
                    if expected < 0 and cycle_interval > 0:
                        expected = expected % float(cycle_interval)

                    # 正常的周期重置：上次已接近 0，这次回到接近 interval
                    is_cycle_reset = (expected_raw <= 0) and (observed_next > float(cycle_interval) * 0.7)

                    if is_cycle_reset:
                        state.next_jump_suspect_count = 0
                    else:
                        diff = observed_next - expected
                        forced_like = abs(abs(diff) - 900.0) < 10.0  # 常见“强制汇报”跳变 ~15min
                        jump_threshold = max(120.0, float(cycle_interval) * 0.15)

                        recent_ra = (now - float(getattr(state, "last_reannounce", 0.0)) < 120.0) or \
                                    (now - float(getattr(state, "last_force_reannounce", 0.0)) < 120.0)

                        if (not forced_like) and (abs(diff) > jump_threshold) and (not recent_ra):
                            state.next_jump_suspect_count += 1
                        else:
                            state.next_jump_suspect_count = max(0, state.next_jump_suspect_count - 1)

                        # 连续两次异常跳变：采用 expected 替代 observed，避免前端倒计时乱跳
                        if state.next_jump_suspect_count >= 2 and not recent_ra:
                            observed_next = max(0.0, min(float(cycle_interval), expected))
                            reannounce_seconds = int(observed_next)
                            fetch_source = "state_calc"

                # 更新观测值（用于下一次推算）
                if reannounce_seconds is not None and reannounce_seconds > 0:
                    state.last_next_remaining = float(reannounce_seconds)
                    state.last_next_update_time = float(now)
            except Exception:
                pass


        # 这里不再重复覆盖 cycle_interval；上面已处理 custom/u2/默认逻辑

        # peerlist方式获取精准时间
        if site_rule and site_rule.peerlist_enabled:
            tid = self._get_cached_tid(torrent)
            publish_time = _publish_time_cache.get(torrent.hash)

            if not tid:
                # 尝试从缓存的 comment URL 提取 TID
                comment_url = _comment_cache.get(torrent.hash, "")
                if comment_url:
                    tracker_urls.append(comment_url)

                # 搜索 TID
                tid, publish_time = await self._search_tid_by_hash(site_rule, torrent)
                if publish_time and state:
                    state.publish_time = publish_time
            elif publish_time and state and not state.publish_time:
                state.publish_time = publish_time

            if tid:
                peerlist_time = await self._get_peerlist_time_cached(
                    site_rule, torrent.hash, tid, now
                )
                if peerlist_time is not None:
                    time_mode = getattr(site_rule, 'peerlist_time_mode', 'elapsed')
                    if time_mode == "remaining":
                        reannounce_seconds = peerlist_time
                        fetch_source = "peerlist_remaining"
                        if state:
                            state.last_announce_time = now + peerlist_time - cycle_interval
                    else:
                        idle_seconds = peerlist_time
                        if state:
                            state.last_announce_time = now - idle_seconds
                            # 与用户脚本一致：max(0, next_announce - now)
                            reannounce_seconds = state.last_announce_time + cycle_interval - now
                            reannounce_seconds = max(0, int(reannounce_seconds))
                        else:
                            reannounce_seconds = max(cycle_interval - idle_seconds, 0)
                        fetch_source = "peerlist_elapsed"

        # 确定剩余时间
        if reannounce_seconds is not None and reannounce_seconds > 0:
            time_left = reannounce_seconds
            if state:
                state.next_announce_time = now + reannounce_seconds
        elif torrent.next_announce_time and torrent.next_announce_time > now:
            time_left = torrent.next_announce_time - now
            fetch_source = fetch_source or "torrent_info"
            if state:
                state.next_announce_time = torrent.next_announce_time
        elif state and state.next_announce_time and state.next_announce_time > now:
            time_left = state.next_announce_time - now
            fetch_source = fetch_source or "saved_state"
        elif state:
            time_left = state.get_time_left(now)
            fetch_source = fetch_source or "state_calc"
        else:
            time_left = cycle_interval
            fetch_source = fetch_source or "estimated"

        # 确保 time_left 在合理范围内
        if time_left < 0:
            time_left = cycle_interval
        elif time_left > cycle_interval * 1.5:
            time_left = cycle_interval

        # 同步 reannounce 缓存（用于脚本式的剩余时间计算）
        if state and 0 < time_left < C.MAX_REANNOUNCE:
            state.cached_tl = float(time_left)
            state.cache_ts = now

        # 更新周期进度和速度
        if state:
            state.total_uploaded = torrent.uploaded or 0
            # 更新卡尔曼滤波速度（确保速度实时更新）
            state.kalman.update(torrent.upload_speed, now)
            state.tracker_speed.record(now, torrent.upload_speed)
            target_speed = site_rule.target_upload_speed if site_rule else 10485760
            sm = float(getattr(site_rule, 'safety_margin', 0.0)) if site_rule else 0.0
            state.update_cycle_progress(target_speed, sm)

        # 动态计算阶段
        cycle_synced = state.cycle_synced if state else False
        if state and state.phase != C.PHASE_IDLE:
            display_phase = state.phase
        else:
            display_phase = get_phase(time_left, cycle_synced, True)

        # 计算种子年龄（用于调试）
        publish_time_val = _publish_time_cache.get(torrent.hash) or (state.publish_time if state else None)
        if publish_time_val and publish_time_val > 0 and publish_time_val <= now + 60:
            torrent_age = now - publish_time_val
            age_source = "publish"
        elif torrent.seeding_time and torrent.seeding_time > 0:
            torrent_age = torrent.seeding_time
            age_source = "seeding"
        else:
            added_ts = torrent.added_time.timestamp() if torrent.added_time else now
            torrent_age = now - added_ts
            age_source = "added"

        return {
            "name": torrent.name[:30] if torrent.name else torrent.hash[:8],
            "tracker": tracker,
            "phase": display_phase,
            "limit": state.current_limit if state else 0,
            "last_limit": state.current_limit if state else 0,
            "time_left": time_left,
            "cycle_synced": state.cycle_synced if state else False,
            "cycle_interval": cycle_interval,
            "announce_interval": cycle_interval,
            "filtered_speed": state.kalman.speed if state else torrent.upload_speed,
            "cycle_progress": state.cycle_progress if state else 0,
            "cycle_time_progress": state.cycle_time_progress if state else 0,
            "cycle_current_upload": state.cycle_current_upload if state else 0,
            "cycle_target_upload": state.cycle_target_upload if state else 0,
            "cycle_avg_speed": state.cycle_avg_speed if state else 0,
            "estimated_completion": state.estimated_completion if state else 0,
            "next_announce_time": state.next_announce_time if state else None,
            "reannounce_raw": reannounce_seconds,
            "time_left_source": fetch_source,
            "interval_source": interval_source,
            # 调试信息
            "torrent_age_days": round(torrent_age / 86400, 1),
            "age_source": age_source,
            "seeding_time": torrent.seeding_time,
        }

    def get_suggested_interval(self) -> float:
        """获取建议的下次检查间隔

        根据所有活跃种子的最小剩余时间动态调整检查频率
        参考 Speed-Limiting-Engine.py 的动态休眠机制

        Returns:
            建议的检查间隔（秒）
        """
        if not self.states:
            return C.DYNAMIC_INTERVAL_MAX

        now = time.time()
        min_time_left = float('inf')

        # 找出所有活跃种子中最小的剩余时间
        for state in self.states.values():
            if state.phase == C.PHASE_IDLE:
                continue  # 跳过不需要限速的种子

            time_left = state.get_time_left(now)
            if time_left > 0:
                min_time_left = min(min_time_left, time_left)

        # 如果没有活跃种子，使用最大间隔
        if min_time_left == float('inf'):
            return C.DYNAMIC_INTERVAL_MAX

        # 根据最小剩余时间确定检查间隔
        if min_time_left <= 5:
            interval = C.DYNAMIC_INTERVAL['critical']
        elif min_time_left <= 15:
            interval = C.DYNAMIC_INTERVAL['urgent']
        elif min_time_left <= 30:
            interval = C.DYNAMIC_INTERVAL['active']
        elif min_time_left <= 60:
            interval = C.DYNAMIC_INTERVAL['normal']
        elif min_time_left <= 120:
            interval = C.DYNAMIC_INTERVAL['relaxed']
        else:
            interval = C.DYNAMIC_INTERVAL['idle']

        # 确保在合理范围内
        return clamp(interval, C.DYNAMIC_INTERVAL_MIN, C.DYNAMIC_INTERVAL_MAX)
