"""
Utility functions for system commands.

This module provides various utility functions used by the system commands,
including logging, cleanup, and validation.
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
import gzip
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

def parse_log_line(line: str) -> Optional[Tuple[datetime, str, str, str]]:
    """
    Parse a log line into timestamp, level, logger, and message.

    Args:
        line: The log line to parse.

    Returns:
        Tuple of (timestamp, level, logger_name, message) or None if parsing fails.
    """
    # Example log format: 2023-11-15 12:34:56,789 - module.name - LEVEL - Message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^ ]+) - ([A-Z]+) - (.+)'
    match = re.match(pattern, line)
    if not match:
        return None
        
    timestamp_str, logger_name, level, message = match.groups()
    try:
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        return timestamp, level, logger_name, message
    except ValueError:
        return None

def get_log_files(log_type: str = 'system') -> List[Path]:
    """
    Get log files for the specified log type.

    Args:
        log_type: Type of logs to retrieve ('system' or 'chat').

    Returns:
        List of Path objects for the log files.
    """
    log_dir = Path.home() / ".ellma" / "logs"
    if log_type == 'system':
        return sorted(log_dir.glob('system.log*'))
    elif log_type == 'chat':
        return sorted(log_dir.glob('chat.log*'))
    return []

def read_logs(log_type: str = 'system', since: Optional[timedelta] = None) -> List[str]:
    """
    Read logs of specified type, optionally filtered by time.

    Args:
        log_type: Type of logs to read ('system' or 'chat').
        since: Optional timedelta to filter logs newer than this duration.

    Returns:
        List of log entries as strings.
    """
    log_files = get_log_files(log_type)
    if not log_files:
        return []
        
    cutoff_time = datetime.now(timezone.utc) - since if since else None
    all_entries = []
    
    for log_file in reversed(log_files):  # Start from most recent logs first
        try:
            # Handle compressed logs
            if log_file.suffix == '.gz':
                with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Process lines in reverse order (newest first)
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                    
                parsed = parse_log_line(line)
                if not parsed:
                    all_entries.append((None, line))
                    continue
                    
                timestamp, level, logger_name, message = parsed
                if cutoff_time and timestamp < cutoff_time:
                    return all_entries  # Stop if we've gone past the cutoff
                    
                all_entries.append((timestamp, f"{timestamp} - {logger_name} - {level} - {message}"))
                
        except Exception as e:
            logger.warning(f"Error reading log file {log_file}: {e}")
            
    return [entry[1] for entry in all_entries if entry[1]]

def get_level_style(level: str) -> str:
    """
    Get rich style for log level.

    Args:
        level: Log level as string.

    Returns:
        Rich style string for the log level.
    """
    styles = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold red'
    }
    return styles.get(level, '')

def get_numeric_log_level(log_entry: str) -> int:
    """
    Get numeric log level from log entry.

    Args:
        log_entry: The log entry to check.

    Returns:
        Numeric log level (matching logging module constants).
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    for level_name, level_num in level_map.items():
        if f" - {level_name} - " in log_entry:
            return level_num
    return logging.DEBUG  # Default to DEBUG if level not found

def cleanup_temp_files() -> int:
    """
    Clean temporary files.

    Returns:
        Number of files cleaned up.
    """
    cleaned_count = 0
    temp_dirs = ["/tmp", "/var/tmp", str(Path.home() / "tmp")]

    for temp_dir in temp_dirs:
        temp_path = Path(temp_dir)
        if temp_path.exists():
            try:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            # Only remove files older than 7 days
                            if file_path.stat().st_mtime < (time.time() - 7 * 24 * 3600):
                                file_path.unlink()
                                cleaned_count += 1
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError) as e:
                logger.warning(f"Error cleaning temp directory {temp_dir}: {e}")

    return cleaned_count

def cleanup_old_logs() -> int:
    """
    Clean old log files.

    Returns:
        Number of log files cleaned up.
    """
    cleaned_count = 0
    log_dirs = ["/var/log", str(Path.home() / ".local" / "share" / "logs")]

    for log_dir in log_dirs:
        log_path = Path(log_dir)
        if log_path.exists():
            try:
                for file_path in log_path.rglob("*.log*"):
                    if file_path.is_file():
                        try:
                            # Remove log files older than 30 days
                            if file_path.stat().st_mtime < (time.time() - 30 * 24 * 3600):
                                file_path.unlink()
                                cleaned_count += 1
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError) as e:
                logger.warning(f"Error cleaning log directory {log_dir}: {e}")

    return cleaned_count

def calculate_health_score(scan_results: Dict[str, Any]) -> int:
    """
    Calculate overall system health score (0-100).

    Args:
        scan_results: Dictionary containing system scan results.

    Returns:
        Health score between 0 and 100.
    """
    score = 100
    resources = scan_results.get("resources", {})

    # CPU usage penalty
    cpu_usage = resources.get("cpu_percent", 0)
    if cpu_usage > 90:
        score -= 30
    elif cpu_usage > 70:
        score -= 15
    elif cpu_usage > 50:
        score -= 5

    # Memory usage penalty
    memory_usage = resources.get("memory", {}).get("percent", 0)
    if memory_usage > 95:
        score -= 25
    elif memory_usage > 85:
        score -= 15
    elif memory_usage > 70:
        score -= 5

    # Disk usage penalty
    storage = scan_results.get("storage", {}).get("disks", {})
    for disk_info in storage.values():
        disk_usage = disk_info.get("percent", 0)
        if disk_usage > 95:
            score -= 20
        elif disk_usage > 85:
            score -= 10
        elif disk_usage > 75:
            score -= 3

    # Security considerations
    security = scan_results.get("security", {})
    open_ports_count = len(security.get("open_ports", []))
    if open_ports_count > 20:
        score -= 10
    elif open_ports_count > 10:
        score -= 5

    return max(0, score)
