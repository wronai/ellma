"""
Network and port utility functions.
"""

import socket
import time
from typing import Optional, Tuple, List, Union
from contextlib import closing

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

def is_port_open(host: str, port: int, timeout: float = 5.0) -> bool:
    """
    Check if a port is open on a host

    Args:
        host: Host to check
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is open
    """
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.debug(f"Error checking port {port} on {host}: {e}")
        return False

def wait_for_port(host: str, port: int, timeout: int = 60, interval: float = 1.0) -> bool:
    """
    Wait for a port to become available

    Args:
        host: Host to check
        port: Port number
        timeout: Maximum wait time in seconds
        interval: Check interval in seconds

    Returns:
        True if port became available within timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(interval)
    return False

def get_free_port() -> int:
    """
    Get a free port number

    Returns:
        Available port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
