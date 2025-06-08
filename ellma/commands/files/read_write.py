"""
File reading and writing operations.

This module handles reading from and writing to files with various encodings and formats.
"""

import json
import csv
import yaml
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO

from ellma.commands.base import BaseCommand, validate_args, log_execution
from ellma.utils.logger import get_logger
from .base_operations import FileOperationsMixin

logger = get_logger(__name__)

class FileReadWrite(FileOperationsMixin, BaseCommand):
    """Handles file reading and writing operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize file read/write operations."""
        super().__init__(*args, **kwargs)
        self.supported_formats = {
            'json': self._read_json,
            'yaml': self._read_yaml,
            'csv': self._read_csv,
            'pickle': self._read_pickle,
            'text': self._read_text
        }
    
    @validate_args(str, str, int, bool)
    @log_execution
    def read(self, file_path: str, 
             encoding: str = 'utf-8', 
             max_lines: Optional[int] = None,
            format_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Read file content with automatic format detection.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding to use
            max_lines: Maximum number of lines to read (for text files)
            format_hint: Optional format hint ('json', 'yaml', 'csv', 'pickle', 'text')
            
        Returns:
            Dictionary containing file content and metadata
        """
        path = Path(file_path).expanduser()
        
        # Validate path
        validation = self._validate_path(path, must_exist=True, must_be_file=True)
        if 'error' in validation:
            return validation
        
        # Get basic file info
        result = self._get_file_metadata(path)
        result.update({
            'is_text': self._is_text_file(path),
            'encoding': encoding,
            'hash': self._calculate_hash(path),
            'content': None
        })
        
        # Determine file format
        format_func = None
        if format_hint and format_hint in self.supported_formats:
            format_func = self.supported_formats[format_hint]
        else:
            # Auto-detect format from extension
            ext = path.suffix.lower()
            if ext in ['.json']:
                format_func = self._read_json
            elif ext in ['.yaml', '.yml']:
                format_func = self._read_yaml
            elif ext == '.csv':
                format_func = self._read_csv
            elif ext in ['.pkl', '.pickle']:
                format_func = self._read_pickle
            else:
                format_func = self._read_text
        
        # Read the file
        try:
            if format_func:
                result['content'] = format_func(path, encoding, max_lines)
                result['format'] = format_hint or ext.lstrip('.')
            else:
                result['error'] = f'Unsupported file format: {path.suffix}'
        except Exception as e:
            result['error'] = f'Error reading file: {str(e)}'
            logger.error(f"Error reading file {path}: {e}", exc_info=True)
        
        return result
    
    @validate_args(str, object, str, bool)
    @log_execution
    def write(self, file_path: str, content: Any,
              encoding: str = 'utf-8', 
              append: bool = False) -> Dict[str, Any]:
        """
        Write content to a file with automatic format handling.
        
        Args:
            file_path: Path to the file to write
            content: Content to write (dict, list, or string)
            encoding: File encoding to use
            append: Whether to append to the file
            
        Returns:
            Dictionary with operation status and metadata
        """
        path = Path(file_path).expanduser()
        
        # Check if parent directory exists
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return {'error': f'Failed to create directory {path.parent}: {e}'}
        
        # Determine write mode
        mode = 'a' if append else 'w'
        
        try:
            # Handle different content types
            if isinstance(content, (dict, list)):
                if path.suffix.lower() == '.json':
                    with open(path, mode + 'b' if 'b' in mode else mode, 
                             encoding=encoding if 'b' not in mode else None) as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)
                elif path.suffix.lower() in ['.yaml', '.yml']:
                    with open(path, mode, encoding=encoding) as f:
                        yaml.dump(content, f, default_flow_style=False)
                else:
                    # Default to JSON for complex types
                    with open(path, mode, encoding=encoding) as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                # Handle string content
                with open(path, mode, encoding=encoding) as f:
                    f.write(str(content))
            
            return {
                'success': True,
                'path': str(path),
                'size': path.stat().st_size if path.exists() else 0
            }
        except Exception as e:
            error_msg = f'Error writing to file {path}: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    # Internal format handlers
    def _read_text(self, path: Path, encoding: str, max_lines: Optional[int] = None) -> str:
        """Read text file content."""
        with open(path, 'r', encoding=encoding) as f:
            if max_lines:
                return ''.join([next(f) for _ in range(max_lines)])
            return f.read()
    
    def _read_json(self, path: Path, encoding: str, *_) -> Any:
        """Read JSON file."""
        with open(path, 'r', encoding=encoding) as f:
            return json.load(f)
    
    def _read_yaml(self, path: Path, encoding: str, *_) -> Any:
        """Read YAML file."""
        with open(path, 'r', encoding=encoding) as f:
            return yaml.safe_load(f)
    
    def _read_csv(self, path: Path, encoding: str, *_) -> List[Dict[str, str]]:
        """Read CSV file as list of dictionaries."""
        with open(path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _read_pickle(self, path: Path, *_) -> Any:
        """Read pickled Python object."""
        with open(path, 'rb') as f:
            return pickle.load(f)
