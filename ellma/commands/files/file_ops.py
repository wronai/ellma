"""
File and directory operations.

This module provides functionality for file and directory operations
such as copy, move, delete, create, and permissions management.
"""

import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ellma.commands.base import BaseCommand, validate_args, log_execution
from ellma.utils.logger import get_logger
from .base_operations import FileOperationsMixin

logger = get_logger(__name__)

class FileManagementOperations(FileOperationsMixin, BaseCommand):
    """Handles file and directory management operations."""
    
    @validate_args(str, str, bool, bool)
    @log_execution
    def copy(self, 
            source: str, 
            destination: str, 
            recursive: bool = False,
            preserve_metadata: bool = True) -> Dict[str, Any]:
        """
        Copy a file or directory.
        
        Args:
            source: Source path (file or directory)
            destination: Destination path
            recursive: Whether to copy directories recursively
            preserve_metadata: Whether to preserve file metadata
            
        Returns:
            Dictionary with operation status and metadata
        """
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        
        # Validate source
        if not src.exists():
            return {'error': f'Source does not exist: {source}'}
        
        # Handle existing destination
        if dst.exists():
            if src.is_file() and dst.is_file():
                return {'error': f'Destination file exists: {destination}'}
            if src.is_dir() and dst.is_file():
                return {'error': f'Destination is a file, not a directory: {destination}'}
        
        try:
            if src.is_file():
                # Copy single file
                shutil.copy2(src, dst) if preserve_metadata else shutil.copy(src, dst)
                return {
                    'success': True,
                    'source': str(src),
                    'destination': str(dst),
                    'size': dst.stat().st_size if dst.exists() else 0
                }
            elif src.is_dir():
                if not recursive:
                    return {'error': f'Source is a directory. Use recursive=True to copy directories'}
                
                # Copy directory
                if dst.exists():
                    # If destination exists, copy into it
                    dst = dst / src.name
                    
                shutil.copytree(
                    src, 
                    dst, 
                    copy_function=shutil.copy2 if preserve_metadata else shutil.copy
                )
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in dst.rglob('*') if f.is_file())
                
                return {
                    'success': True,
                    'source': str(src),
                    'destination': str(dst),
                    'files_copied': sum(1 for _ in dst.rglob('*') if _.is_file()),
                    'size': total_size
                }
            else:
                return {'error': f'Unsupported source type: {source}'}
                
        except Exception as e:
            error_msg = f'Error copying {source} to {destination}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, str, bool)
    @log_execution
    def move(self, 
            source: str, 
            destination: str,
            overwrite: bool = False) -> Dict[str, Any]:
        """
        Move or rename a file or directory.
        
        Args:
            source: Source path (file or directory)
            destination: Destination path
            overwrite: Whether to overwrite existing destination
            
        Returns:
            Dictionary with operation status and metadata
        """
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        
        # Validate source
        if not src.exists():
            return {'error': f'Source does not exist: {source}'}
        
        # Handle existing destination
        if dst.exists():
            if not overwrite:
                return {'error': f'Destination exists: {destination}. Use overwrite=True to overwrite'}
            
            # Remove existing destination if overwrite is True
            try:
                if dst.is_file() or dst.is_symlink():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
            except Exception as e:
                return {'error': f'Failed to remove existing destination: {e}'}
        
        try:
            # Create parent directory if it doesn't exist
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform the move
            shutil.move(str(src), str(dst))
            
            return {
                'success': True,
                'source': str(src),
                'destination': str(dst),
                'size': dst.stat().st_size if dst.exists() and dst.is_file() else 0
            }
            
        except Exception as e:
            error_msg = f'Error moving {source} to {destination}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, bool, bool)
    @log_execution
    def delete(self, path: str, recursive: bool = False, force: bool = False) -> Dict[str, Any]:
        """
        Delete a file or directory.
        
        Args:
            path: Path to delete
            recursive: Whether to delete directories recursively
            force: Whether to force deletion (ignore read-only files)
            
        Returns:
            Dictionary with operation status
        """
        target = Path(path).expanduser()
        
        if not target.exists():
            return {'error': f'Path does not exist: {path}'}
        
        try:
            if target.is_file() or target.is_symlink():
                # Handle read-only files if force is True
                if force and os.name == 'nt':  # Windows
                    os.chmod(target, stat.S_IWRITE)
                target.unlink()
            elif target.is_dir():
                if not recursive:
                    return {'error': f'Cannot delete directory. Use recursive=True to delete directories'}
                
                # Handle read-only files in directory if force is True
                if force and os.name == 'nt':  # Windows
                    for root, dirs, files in os.walk(target, topdown=False):
                        for name in files:
                            file_path = Path(root) / name
                            os.chmod(file_path, stat.S_IWRITE)
                
                shutil.rmtree(target)
            
            return {
                'success': True,
                'path': str(target),
                'deleted': True
            }
            
        except Exception as e:
            error_msg = f'Error deleting {path}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, str, bool, bool)
    @log_execution
    def create_directory(self, 
                       path: str, 
                       parents: bool = True, 
                       exist_ok: bool = True) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            path: Directory path to create
            parents: Whether to create parent directories
            exist_ok: Whether to ignore if directory already exists
            
        Returns:
            Dictionary with operation status and metadata
        """
        target = Path(path).expanduser()
        
        try:
            target.mkdir(parents=parents, exist_ok=exist_ok)
            return {
                'success': True,
                'path': str(target),
                'exists': target.exists(),
                'is_dir': target.is_dir()
            }
        except Exception as e:
            error_msg = f'Error creating directory {path}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, str, bool)
    @log_execution
    def create_temp_file(self, 
                       prefix: str = 'tmp', 
                       suffix: str = '',
                       delete_on_close: bool = False) -> Dict[str, Any]:
        """
        Create a temporary file.
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix
            delete_on_close: Whether to delete file when closed
            
        Returns:
            Dictionary with file information
        """
        try:
            with tempfile.NamedTemporaryFile(
                prefix=prefix,
                suffix=suffix,
                delete=delete_on_close
            ) as temp_file:
                path = Path(temp_file.name)
                return {
                    'success': True,
                    'path': str(path),
                    'name': path.name,
                    'parent': str(path.parent),
                    'size': path.stat().st_size if path.exists() else 0
                }
        except Exception as e:
            error_msg = f'Error creating temporary file: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, str, bool)
    @log_execution
    def set_permissions(self, 
                       path: str, 
                       mode: str,
                       recursive: bool = False) -> Dict[str, Any]:
        """
        Set file or directory permissions.
        
        Args:
            path: Path to file or directory
            mode: Permission mode in octal (e.g., '755', '644')
            recursive: Whether to apply permissions recursively
            
        Returns:
            Dictionary with operation status
        """
        target = Path(path).expanduser()
        
        if not target.exists():
            return {'error': f'Path does not exist: {path}'}
        
        try:
            # Convert mode string to octal
            mode_int = int(mode, 8)
            
            if recursive and target.is_dir():
                # Apply to directory and all contents
                for root, dirs, files in os.walk(target):
                    os.chmod(root, mode_int)
                    for name in files:
                        os.chmod(Path(root) / name, mode_int)
            else:
                os.chmod(target, mode_int)
            
            return {
                'success': True,
                'path': str(target),
                'permissions': oct(os.stat(target).st_mode)[-3:]
            }
            
        except Exception as e:
            error_msg = f'Error setting permissions for {path}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
