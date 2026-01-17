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
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Deque
from collections import deque
from dataclasses import dataclass, field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SpeedLimitConfig, SpeedLimitSite, SpeedLimitRecord, Downloader, SystemSettings
from app.services.downloader import create_downloader, TorrentInfo
from app.utils import get_tracker_domain, get_logger

logger = get_logger('pt_manager.speed_limit')


# ════════════════════════════════════════════════════════════════════════════════
# 常量配置
# ════════════════════════════════════════════════════════════════════════════════
class C:
    """配置常量"""
    PHASE_WARMUP = "warmup"
    PHASE_CATCH = "catch"
    PHASE_STEADY = "steady"
    PHASE_FINISH = "finish"

    # 阶段时间阈值（秒）
    WARMUP_TIME = 30
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

    # 强制汇报相关
    REANNOUNCE_WAIT_LIMIT = 5120      # 等待汇报时的限速 (KB)
    REANNOUNCE_MIN_INTERVAL = 900     # 最小汇报间隔（秒）
    REANNOUNCE_SPEED_SAMPLES = 300    # 速度采样数

    # Kalman滤波参数
    KALMAN_Q_SPEED = 100.0
    KALMAN_Q_ACCEL = 10.0
    KALMAN_R = 400.0

    # 速度窗口（秒）
    SPEED_WINDOWS = [5, 10, 30, 60]

    # 窗口权重
    WINDOW_WEIGHTS = {
        'warmup': {5: 0.5, 10: 0.3, 30: 0.15, 60: 0.05},
        'catch': {5: 0.4, 10: 0.35, 30: 0.2, 60: 0.05},
        'steady': {5: 0.3, 10: 0.35, 30: 0.25, 60: 0.1},
        'finish': {5: 0.5, 10: 0.3, 30: 0.15, 60: 0.05},
    }

    # PID参数（按阶段）
    PID_PARAMS = {
        'warmup': {'kp': 0.3, 'ki': 0.05, 'kd': 0.02, 'headroom': 1.03},
        'catch': {'kp': 0.5, 'ki': 0.08, 'kd': 0.04, 'headroom': 1.02},
        'steady': {'kp': 0.6, 'ki': 0.15, 'kd': 0.08, 'headroom': 1.01},
        'finish': {'kp': 0.8, 'ki': 0.2, 'kd': 0.1, 'headroom': 1.005},
    }

    # 量化步长
    QUANT_STEPS = {
        'warmup': 4096,
        'catch': 2048,
        'steady': 1024,
        'finish': 512,
    }


# ════════════════════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════════════════════
def safe_div(a: float, b: float, default: float = 0) -> float:
    """安全除法"""
    try:
        if b == 0 or abs(b) < 1e-10:
            return default
        return a / b
    except:
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在范围内"""
    return max(min_val, min(max_val, value))


def estimate_announce_interval(time_ref: float) -> int:
    """根据种子时间估算汇报间隔"""
    age = time.time() - time_ref
    if age < 7 * 86400:
        return C.ANNOUNCE_INTERVAL_NEW
    elif age < 30 * 86400:
        return C.ANNOUNCE_INTERVAL_WEEK
    return C.ANNOUNCE_INTERVAL_OLD


def get_phase(time_left: float, synced: bool) -> str:
    """根据剩余时间确定阶段"""
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
        self._integral_limit = 0.3
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
    """多窗口速度追踪器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._samples: Deque[Tuple[float, float]] = deque(maxlen=1200)

    def record(self, now: float, speed: float):
        """记录速度采样"""
        with self._lock:
            self._samples.append((now, speed))

    def get_weighted_avg(self, now: float, phase: str) -> float:
        """获取加权平均速度"""
        weights = C.WINDOW_WEIGHTS.get(phase, C.WINDOW_WEIGHTS['steady'])
        with self._lock:
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
        with self._lock:
            samples = [(t, s) for t, s in self._samples if now - t <= window]

        if len(samples) < 5:
            return 0.0

        mid = len(samples) // 2
        first = sum(s for _, s in samples[:mid]) / mid
        second = sum(s for _, s in samples[mid:]) / (len(samples) - mid)
        return safe_div(second - first, first, 0)

    def clear(self):
        with self._lock:
            self._samples.clear()

    def get_state(self) -> Dict:
        with self._lock:
            return {'samples': list(self._samples)}

    def set_state(self, state: Dict):
        with self._lock:
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

    # 上传量追踪
    total_uploaded: int = 0
    cycle_start_uploaded: int = 0
    cycle_synced: bool = False
    cycle_interval: float = 0.0
    last_jump: float = 0.0

    # 汇报状态
    last_announce_time: Optional[float] = None
    last_reannounce: float = 0.0
    reannounced_this_cycle: bool = False
    waiting_reannounce: bool = False
    next_announce_time: Optional[float] = None
    announce_interval: Optional[int] = None

    # 控制器
    pid: PIDController = field(default_factory=PIDController)
    kalman: ExtendedKalman = field(default_factory=ExtendedKalman)
    tracker_speed: MultiWindowSpeedTracker = field(default_factory=MultiWindowSpeedTracker)

    # 当前状态
    current_limit: int = 0
    phase: str = C.PHASE_WARMUP

    def get_time_left(self, now: float) -> float:
        """获取距离下次汇报的剩余时间"""
        if self.next_announce_time and self.next_announce_time > 0:
            remaining = max(0, self.next_announce_time - now)
            if self.announce_interval and remaining > self.announce_interval:
                remaining = self.announce_interval
            return remaining
        if self.last_announce_time and self.last_announce_time > 0:
            interval = self.get_announce_interval()
            next_announce = self.last_announce_time + interval
            return max(0, next_announce - now)

        # 未同步时估算
        if self.cycle_synced and self.cycle_interval > 0:
            return max(1, self.cycle_interval)

        if self.announce_interval:
            return max(1, self.announce_interval)
        return estimate_announce_interval(self.time_added)

    def get_announce_interval(self) -> int:
        """获取汇报间隔"""
        if self.cycle_synced and self.cycle_interval > 0:
            return int(self.cycle_interval)

        if self.publish_time:
            return estimate_announce_interval(self.publish_time)

        return estimate_announce_interval(self.time_added)

    def sync_cycle(self, total_uploaded: int, now: float):
        """同步汇报周期 - 通过检测上传量跳变"""
        if total_uploaded <= self.total_uploaded:
            self.total_uploaded = total_uploaded
            return

        # 检测上传量跳变（汇报）
        delta = total_uploaded - self.total_uploaded
        self.total_uploaded = total_uploaded

        # 如果上传量突然跳变很多，说明发生了汇报
        if delta > 1024 * 1024:  # 1MB 阈值
            if self.last_jump > 0:
                interval = now - self.last_jump
                if 60 < interval < 7200:  # 1分钟到2小时之间
                    self.cycle_interval = interval
                    self.cycle_synced = True
                    self.last_announce_time = now
                    logger.info(f"[{self.name[:20]}] 检测到汇报周期: {int(interval)}秒")

            self.last_jump = now
            self.cycle_start_uploaded = total_uploaded
            self.reannounced_this_cycle = False
            self.waiting_reannounce = False

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
            'cycle_start_uploaded': self.cycle_start_uploaded,
            'cycle_synced': self.cycle_synced,
            'cycle_interval': self.cycle_interval,
            'last_jump': self.last_jump,
            'last_announce_time': self.last_announce_time,
            'last_reannounce': self.last_reannounce,
            'reannounced_this_cycle': self.reannounced_this_cycle,
            'waiting_reannounce': self.waiting_reannounce,
            'next_announce_time': self.next_announce_time,
            'announce_interval': self.announce_interval,
            'current_limit': self.current_limit,
            'phase': self.phase,
            'pid_state': self.pid.get_state(),
            'kalman_state': self.kalman.get_state(),
            'tracker_state': self.tracker_speed.get_state(),
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
            cycle_start_uploaded=data.get('cycle_start_uploaded', 0),
            cycle_synced=data.get('cycle_synced', False),
            cycle_interval=data.get('cycle_interval', 0),
            last_jump=data.get('last_jump', 0),
            last_announce_time=data.get('last_announce_time'),
            last_reannounce=data.get('last_reannounce', 0),
            reannounced_this_cycle=data.get('reannounced_this_cycle', False),
            waiting_reannounce=data.get('waiting_reannounce', False),
            next_announce_time=data.get('next_announce_time'),
            announce_interval=data.get('announce_interval'),
            current_limit=data.get('current_limit', 0),
            phase=data.get('phase', C.PHASE_WARMUP),
        )

        if 'pid_state' in data:
            state.pid.set_state(data['pid_state'])
        if 'kalman_state' in data:
            state.kalman.set_state(data['kalman_state'])
        if 'tracker_state' in data:
            state.tracker_speed.set_state(data['tracker_state'])

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
# 主服务类
# ════════════════════════════════════════════════════════════════════════════════
class SpeedLimiterService:
    """动态限速服务 - 完整版"""

    STATE_KEY = "speed_limiter_state"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.states: Dict[str, TorrentState] = {}
        self._running = False
        self._lock = threading.Lock()

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

    async def save_state(self):
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
            self.states[torrent.hash] = TorrentState(
                hash=torrent.hash,
                name=torrent.name,
                tracker=tracker,
                time_added=torrent.added_time.timestamp() if torrent.added_time else time.time(),
                total_size=torrent.size,
                total_uploaded=torrent.uploaded,
                next_announce_time=torrent.next_announce_time,
                announce_interval=torrent.announce_interval,
            )
        else:
            self.states[torrent.hash].next_announce_time = torrent.next_announce_time
            self.states[torrent.hash].announce_interval = torrent.announce_interval
        return self.states[torrent.hash]

    def _calculate_limit(
        self,
        state: TorrentState,
        current_speed: float,
        target_speed: float,
        now: float
    ) -> int:
        """计算限速值"""
        # 更新卡尔曼滤波
        filtered_speed, accel = state.kalman.update(current_speed, now)

        # 记录速度
        state.tracker_speed.record(now, filtered_speed)

        # 获取加权平均速度
        tracked_speed = state.tracker_speed.get_weighted_avg(now, state.phase)
        if tracked_speed <= 0:
            tracked_speed = filtered_speed

        # 获取剩余时间和阶段
        if state.cycle_synced:
            time_left = state.get_time_left(now)
            phase = get_phase(time_left, True)
        else:
            time_left = state.get_time_left(now)
            phase = C.PHASE_WARMUP if (now - state.time_added) <= C.WARMUP_TIME else C.PHASE_CATCH
        state.phase = phase

        # 更新PID参数
        state.pid.set_phase(phase)

        # 阶段特定限速计算
        if phase == C.PHASE_WARMUP:
            # 预热阶段不限速
            return 0

        elif phase == C.PHASE_CATCH:
            # 追赶阶段：允许较高速度
            ratio = safe_div(tracked_speed, target_speed, 0.5)
            multiplier = clamp(2.0 - ratio, 1.0, 2.0)
            return int(target_speed * multiplier)

        elif phase == C.PHASE_STEADY:
            # 稳定阶段：PID精细控制
            pid_output = state.pid.update(target_speed, tracked_speed, now)
            trend = state.tracker_speed.get_recent_trend(now)

            base_limit = target_speed * pid_output

            # 趋势调整
            if trend > 0.05:
                base_limit *= 0.98
            elif trend < -0.05:
                base_limit *= 1.02

            limit = int(base_limit)
            return AdaptiveQuantizer.quantize(limit, phase, tracked_speed, target_speed, trend)

        else:  # PHASE_FINISH
            # 完成阶段：严格控制
            remaining_quota = target_speed * time_left
            safety_limit = remaining_quota / max(time_left, 1) * 0.9

            if tracked_speed > target_speed:
                # 超速，紧急降低
                reduction = (tracked_speed - target_speed) * 0.5
                safety_limit -= reduction

            limit = int(max(C.MIN_LIMIT, safety_limit))
            return AdaptiveQuantizer.quantize(limit, phase, tracked_speed, target_speed)

    async def apply_limits(self) -> Dict[str, Any]:
        """应用限速"""
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

        for downloader in downloaders:
            try:
                client = create_downloader(downloader)
                if not await client.connect():
                    continue

                torrents = await client.get_torrents()

                for torrent in torrents:
                    if torrent.status not in ['seeding', 'downloading']:
                        continue

                    tracker = get_tracker_domain(torrent.tracker)
                    if not tracker:
                        continue

                    # 获取目标速度
                    site_rule = site_rule_map.get(tracker)
                    if site_rule:
                        target_speed = site_rule.target_upload_speed
                    else:
                        target_speed = config.target_upload_speed

                    if target_speed <= 0:
                        continue

                    # 获取或创建状态
                    state = self._get_or_create_state(torrent, tracker)

                    # 同步周期
                    state.sync_cycle(torrent.uploaded, now)

                    # 计算限速
                    limit = self._calculate_limit(state, torrent.upload_speed, target_speed, now)

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
                            state.current_limit = limit
                        except Exception as e:
                            logger.error(f"设置限速失败: {e}")

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
                        "cycle_interval": state.cycle_interval,
                    }

                    # 记录到数据库
                    record = SpeedLimitRecord(
                        tracker_domain=tracker,
                        current_speed=torrent.upload_speed,
                        target_speed=target_speed,
                        limit_applied=limit,
                        phase=state.phase,
                    )
                    self.db.add(record)

                await client.disconnect()

            except Exception as e:
                logger.error(f"处理下载器 {downloader.name} 失败: {e}")

        await self.db.commit()

        # 定期保存状态
        await self.save_state()

        return {
            "enabled": True,
            "torrents": results,
            "count": len(results),
        }

    async def clear_limits(self):
        """清除所有限速"""
        result = await self.db.execute(
            select(Downloader).where(Downloader.enabled == True)
        )
        downloaders = result.scalars().all()

        for downloader in downloaders:
            try:
                client = create_downloader(downloader)
                if await client.connect():
                    torrents = await client.get_torrents()
                    for torrent in torrents:
                        await client.set_torrent_upload_limit(torrent.hash, 0)
                    await client.disconnect()
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
            status[hash] = {
                "name": state.name,
                "tracker": state.tracker,
                "phase": state.phase,
                "limit": state.current_limit,
                "last_limit": state.current_limit,
                "time_left": state.get_time_left(now),
                "cycle_synced": state.cycle_synced,
                "cycle_interval": state.cycle_interval,
                "filtered_speed": state.kalman.speed,
            }

        return status
