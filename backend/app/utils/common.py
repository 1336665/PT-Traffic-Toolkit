"""Common utility functions shared across services"""

import re
from urllib.parse import urlparse
from typing import Optional


# Size unit multipliers (to bytes)
SIZE_UNITS = {
    'B': 1,
    'KB': 1024,
    'KIB': 1024,
    'MB': 1024 ** 2,
    'MIB': 1024 ** 2,
    'GB': 1024 ** 3,
    'GIB': 1024 ** 3,
    'TB': 1024 ** 4,
    'TIB': 1024 ** 4,
}

# Time unit multipliers (to seconds)
TIME_UNITS = {
    'seconds': 1,
    'minutes': 60,
    'hours': 3600,
    'days': 86400,
}

# Speed unit multipliers (to bytes/s)
SPEED_UNITS = {
    'B/s': 1,
    'KB/s': 1024,
    'MB/s': 1024 ** 2,
}


def parse_size(size_str: str) -> float:
    """
    Parse size string to bytes.

    Examples:
        "10GB" -> 10737418240
        "500 MB" -> 524288000
        "1.5 TiB" -> 1649267441664
    """
    if not size_str:
        return 0

    size_str = size_str.strip().upper()

    match = re.match(r'([\d.]+)\s*([A-Z]+)?', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2) or 'B'
        return value * SIZE_UNITS.get(unit, 1)
    return 0


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to hours.

    Supports Chinese and English formats:
        "1天" -> 24
        "2小时" -> 2
        "30分钟" -> 0 (rounds to 0)
        "1d 2h" -> 26
    """
    if not duration_str:
        return 0

    hours = 0

    # Match patterns like "1天", "2小时", "30分钟", "1d", "2h", "30m"
    day_match = re.search(r'(\d+)\s*[天日dD]', duration_str)
    hour_match = re.search(r'(\d+)\s*[时小時hH]', duration_str)
    min_match = re.search(r'(\d+)\s*[分mM]', duration_str)

    if day_match:
        hours += int(day_match.group(1)) * 24
    if hour_match:
        hours += int(hour_match.group(1))
    if min_match:
        hours += int(min_match.group(1)) / 60

    return int(hours)


def get_tracker_domain(tracker_url: str) -> Optional[str]:
    """
    Extract domain from tracker URL.

    Examples:
        "https://tracker.example.com:8080/announce" -> "tracker.example.com"
        "udp://tracker.example.com:6969" -> "tracker.example.com"
    """
    if not tracker_url:
        return None

    try:
        parsed = urlparse(tracker_url)
        domain = parsed.netloc
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        return domain if domain else None
    except Exception:
        return None


def convert_size_unit(value: float, from_unit: str, to_unit: str = 'B') -> float:
    """Convert size between units"""
    bytes_value = value * SIZE_UNITS.get(from_unit.upper(), 1)
    return bytes_value / SIZE_UNITS.get(to_unit.upper(), 1)


def convert_time_unit(value: float, from_unit: str, to_unit: str = 'seconds') -> float:
    """Convert time between units"""
    seconds_value = value * TIME_UNITS.get(from_unit.lower(), 1)
    return seconds_value / TIME_UNITS.get(to_unit.lower(), 1)


def format_size(size_bytes: float) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_speed(speed_bytes: float) -> str:
    """Format bytes/s to human readable string"""
    return f"{format_size(speed_bytes)}/s"
