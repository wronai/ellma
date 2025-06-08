"""
Input validation and sanitization utilities.
"""

import re
from typing import Optional, Union, Pattern, Any
from pathlib import Path
from ipaddress import ip_address, IPv4Address, IPv6Address

# Common regex patterns
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', 
    re.IGNORECASE
)

def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email appears valid
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email))

def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL appears valid
    """
    if not url or not isinstance(url, str):
        return False
    return bool(URL_REGEX.match(url))

def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
    """
    Validate IP address.

    Args:
        ip: IP address to validate
        version: IP version (4 or 6), None for any

    Returns:
        True if IP address is valid
    """
    try:
        addr = ip_address(ip)
        if version is not None:
            if version == 4 and not isinstance(addr, IPv4Address):
                return False
            if version == 6 and not isinstance(addr, IPv6Address):
                return False
        return True
    except ValueError:
        return False

def validate_regex(pattern: Union[str, Pattern[str]], value: str) -> bool:
    """
    Validate string against a regex pattern.

    Args:
        pattern: Regex pattern (string or compiled pattern)
        value: String to validate

    Returns:
        True if string matches the pattern
    """
    if not isinstance(value, str):
        return False
    
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    return bool(pattern.match(value))

def validate_file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if a file exists and is accessible.

    Args:
        file_path: Path to the file

    Returns:
        True if file exists and is accessible
    """
    try:
        path = Path(file_path).resolve()
        return path.is_file() and os.access(str(path), os.R_OK)
    except (TypeError, ValueError, OSError):
        return False

def validate_directory(directory: Union[str, Path], create: bool = False) -> bool:
    """
    Validate a directory path.

    Args:
        directory: Path to the directory
        create: If True, create directory if it doesn't exist

    Returns:
        True if directory exists and is accessible (or was created)
    """
    try:
        path = Path(directory).resolve()
        if path.is_dir():
            return os.access(str(path), os.W_OK)
        if create:
            path.mkdir(parents=True, exist_ok=True)
            return path.is_dir()
        return False
    except (TypeError, ValueError, OSError):
        return False

def validate_type(value: Any, expected_type: type) -> bool:
    """
    Validate value type.

    Args:
        value: Value to check
        expected_type: Expected type (or tuple of types)

    Returns:
        True if value is of expected type
    """
    return isinstance(value, expected_type)
