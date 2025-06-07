"""
File and I/O utility functions.
"""

import os
import hashlib
import tempfile
from pathlib import Path
from typing import Union, Optional, BinaryIO

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file contents

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)

    Returns:
        Hexadecimal hash string
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = getattr(hashlib, algorithm.lower(), None)
    if not hash_func:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    h = hash_func()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_file_size_human(size_bytes: int) -> str:
    """
    Convert bytes to human readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.2f}{units[i]}"

def create_temp_file(suffix: str = '', prefix: str = 'ellma_', content: str = '') -> Path:
    """
    Create temporary file with content

    Args:
        suffix: File suffix
        prefix: File prefix
        content: File content

    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as f:
        if content:
            f.write(content.encode('utf-8'))
        return Path(f.name)

def cleanup_temp_files(pattern: str = 'ellma_*') -> None:
    """
    Clean up temporary files matching pattern

    Args:
        pattern: File pattern to match
    """
    import glob
    import os
    
    for file_path in glob.glob(os.path.join(tempfile.gettempdir(), pattern)):
        try:
            os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file {file_path}: {e}")

def is_newer_than(file_path: Union[str, Path], hours: int) -> bool:
    """
    Check if file is newer than specified hours

    Args:
        file_path: Path to file
        hours: Hours threshold

    Returns:
        True if file is newer than threshold
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    
    file_time = file_path.stat().st_mtime
    threshold_time = time.time() - (hours * 3600)
    return file_time > threshold_time
