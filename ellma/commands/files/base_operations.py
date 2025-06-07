"""
Base file operations for the File Commands module.

This module provides core file operations used by other file command modules.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class FileOperationsMixin:
    """Mixin class providing core file operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize file operations mixin."""
        super().__init__(*args, **kwargs)
        self.max_file_size = 100 * 1024 * 1024  # 100MB default limit
        self.text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', 
            '.json', '.yaml', '.yml', '.xml', '.csv'
        }
        self.binary_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', 
            '.zip', '.tar', '.gz', '.exe', '.bin'
        }
    
    def _is_text_file(self, path: Path) -> bool:
        """Check if a file is a text file based on extension and content."""
        # First check by extension
        ext = path.suffix.lower()
        if ext in self.text_extensions:
            return True
        if ext in self.binary_extensions:
            return False
            
        # Fallback to content detection
        try:
            with open(path, 'rb') as f:
                sample = f.read(1024)
                # Check for null bytes which indicate binary
                if b'\x00' in sample:
                    return False
                # Try to decode as text
                try:
                    sample.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    return False
        except Exception as e:
            logger.warning(f"Error checking if file is text: {e}")
            return False
    
    def _calculate_hash(self, path: Path, algorithm: str = 'sha256') -> str:
        """Calculate file hash."""
        hash_func = getattr(hashlib, algorithm, hashlib.sha256)
        hasher = hash_func()
        
        try:
            with open(path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {path}: {e}")
            return ""
    
    def _get_file_metadata(self, path: Path) -> Dict[str, Any]:
        """Get basic file metadata."""
        try:
            stat_info = path.stat()
            return {
                'path': str(path),
                'size': stat_info.st_size,
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'permissions': oct(stat_info.st_mode)[-3:],
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'mime_type': mimetypes.guess_type(str(path))[0]
            }
        except Exception as e:
            logger.error(f"Error getting file metadata for {path}: {e}")
            return {}
    
    def _validate_path(self, path: Path, must_exist: bool = True, must_be_file: bool = False) -> Dict[str, Any]:
        """Validate a file path."""
        if not path.exists() and must_exist:
            return {'error': f'Path does not exist: {path}'}
            
        if must_be_file and path.exists() and not path.is_file():
            return {'error': f'Path is not a file: {path}'}
            
        if path.exists() and path.is_file():
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return {'error': f'File too large: {file_size} bytes (max: {self.max_file_size})'}
                
        return {'valid': True}
