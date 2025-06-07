"""
Time and date utility functions.
"""

import time
from datetime import datetime, timedelta
from typing import Union, Optional

def get_timestamp(format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Get current timestamp as string.

    Args:
        format_str: Format string for datetime

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)

def parse_timestamp(timestamp_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> datetime:
    """
    Parse timestamp string to datetime.

    Args:
        timestamp_str: Timestamp string to parse
        format_str: Format string for datetime

    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp_str, format_str)

def days_ago(days: int) -> datetime:
    """
    Get datetime object for N days ago.

    Args:
        days: Number of days ago

    Returns:
        Datetime object
    """
    return datetime.now() - timedelta(days=days)

def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds)}s"
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)}h {int(minutes)}m"
    
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h"

def time_since(timestamp: Union[datetime, float, int]) -> str:
    """
    Get human readable time since given timestamp.

    Args:
        timestamp: Timestamp (datetime, Unix timestamp, or string)

    Returns:
        Human readable time difference (e.g., "2 hours ago")
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = timestamp
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    if diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "just now"

def is_weekday(date: Optional[datetime] = None) -> bool:
    """
    Check if given date is a weekday.

    Args:
        date: Date to check (default: today)

    Returns:
        True if date is a weekday (Mon-Fri)
    """
    if date is None:
        date = datetime.now()
    return date.weekday() < 5  # 0=Monday, 6=Sunday
