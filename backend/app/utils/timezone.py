"""Timezone helpers.

The project stores timestamps in the DB as **naive UTC** datetimes
(`datetime.utcnow`).

For any "today / week / month" style statistics we should calculate
boundaries in the server's **local timezone** and then convert those
boundaries back to naive UTC for DB comparisons.

For chart grouping by date, SQLite supports the 'localtime' modifier.
When the container/system timezone is set correctly (e.g. via TZ env var
or /etc/localtime), `date(created_at, 'localtime')` will group records by
local calendar day (including DST transitions).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def get_local_tzinfo():
    """Return the server's local timezone.

    Preference order:
    1) TZ environment variable (if present and zoneinfo available)
    2) OS-configured local timezone (datetime.now().astimezone())
    3) UTC fallback
    """

    tz_name = os.environ.get("TZ")
    if tz_name and ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            # If TZ is invalid, fall back to OS local tz
            pass

    try:
        return datetime.now().astimezone().tzinfo or timezone.utc
    except Exception:
        return timezone.utc


def to_utc_naive(dt: datetime) -> datetime:
    """Convert an aware datetime to naive UTC.

    If dt is naive, assume it already represents UTC.
    """
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def local_day_start_utc(ref_utc: Optional[datetime] = None) -> datetime:
    """Return local midnight boundary (start of day) as naive UTC."""
    tz = get_local_tzinfo()
    if ref_utc is None:
        ref_local = datetime.now(tz)
    else:
        if ref_utc.tzinfo is None:
            ref_utc = ref_utc.replace(tzinfo=timezone.utc)
        ref_local = ref_utc.astimezone(tz)

    local_start = ref_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return to_utc_naive(local_start)


def local_week_start_utc(ref_utc: Optional[datetime] = None, week_start: int = 0) -> datetime:
    """Return local week start (Monday by default) as naive UTC.

    Args:
        ref_utc: reference time in UTC (naive or aware). If None, uses now.
        week_start: 0=Monday ... 6=Sunday
    """
    tz = get_local_tzinfo()
    if ref_utc is None:
        ref_local = datetime.now(tz)
    else:
        if ref_utc.tzinfo is None:
            ref_utc = ref_utc.replace(tzinfo=timezone.utc)
        ref_local = ref_utc.astimezone(tz)

    local_day_start = ref_local.replace(hour=0, minute=0, second=0, microsecond=0)
    delta_days = (local_day_start.weekday() - week_start) % 7
    week_start_local = local_day_start - timedelta(days=delta_days)
    return to_utc_naive(week_start_local)


def local_month_start_utc(ref_utc: Optional[datetime] = None) -> datetime:
    """Return local month start (1st 00:00) as naive UTC."""
    tz = get_local_tzinfo()
    if ref_utc is None:
        ref_local = datetime.now(tz)
    else:
        if ref_utc.tzinfo is None:
            ref_utc = ref_utc.replace(tzinfo=timezone.utc)
        ref_local = ref_utc.astimezone(tz)

    local_day_start = ref_local.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start_local = local_day_start.replace(day=1)
    return to_utc_naive(month_start_local)


def local_day_range_utc(days: int, ref_utc: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """Return a (start_utc, end_utc) range for N local days.

    The range covers full local days: [start_local_midnight, end_local_midnight).
    """
    if days <= 0:
        days = 1

    tz = get_local_tzinfo()
    if ref_utc is None:
        ref_local = datetime.now(tz)
    else:
        if ref_utc.tzinfo is None:
            ref_utc = ref_utc.replace(tzinfo=timezone.utc)
        ref_local = ref_utc.astimezone(tz)

    today_local = ref_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_local = today_local - timedelta(days=days - 1)
    end_local = today_local + timedelta(days=1)

    return to_utc_naive(start_local), to_utc_naive(end_local)
