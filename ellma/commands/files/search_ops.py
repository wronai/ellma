"""
File search and directory operations.

This module provides functionality for searching files and directories,
listing directory contents, and performing batch operations.
"""

import os
import fnmatch
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Generator, Union, Pattern
from datetime import datetime, timedelta

from ellma.commands.base import BaseCommand, validate_args, log_execution
from ellma.utils.logger import get_logger
from .base_operations import FileOperationsMixin

logger = get_logger(__name__)

class FileSearchOperations(FileOperationsMixin, BaseCommand):
    """Handles file search and directory operations."""
    
    @validate_args(str, str, bool, bool, int, int)
    @log_execution
    def find_files(self, 
                  directory: str, 
                  pattern: str = '*',
                  recursive: bool = True,
                  include_dirs: bool = False,
                  max_depth: Optional[int] = None,
                  max_results: int = 100) -> Dict[str, Any]:
        """
        Find files matching a pattern.
        
        Args:
            directory: Base directory to search in
            pattern: Glob pattern to match files against
            recursive: Whether to search recursively in subdirectories
            include_dirs: Whether to include directories in results
            max_depth: Maximum depth to search (None for unlimited)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing matching files and metadata
        """
        base_path = Path(directory).expanduser()
        
        if not base_path.exists():
            return {'error': f'Directory not found: {directory}'}
        if not base_path.is_dir():
            return {'error': f'Path is not a directory: {directory}'}
        
        try:
            results = []
            count = 0
            
            for file_path in self._walk_directory(base_path, pattern, recursive, include_dirs, max_depth):
                if count >= max_results:
                    break
                    
                file_info = self._get_file_metadata(file_path)
                if file_info:
                    results.append(file_info)
                    count += 1
            
            return {
                'directory': str(base_path),
                'pattern': pattern,
                'matches_found': len(results),
                'files': results
            }
            
        except Exception as e:
            error_msg = f'Error searching files: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    @validate_args(str, str, str, bool, int, int)
    @log_execution
    def search_content(self, 
                      directory: str, 
                      search_term: str,
                      file_pattern: str = '*',
                      case_sensitive: bool = False,
                      max_matches: int = 100,
                      max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for text content in files.
        
        Args:
            directory: Base directory to search in
            search_term: Text or regex pattern to search for
            file_pattern: Glob pattern to filter files
            case_sensitive: Whether the search is case-sensitive
            max_matches: Maximum number of matches to return
            max_depth: Maximum depth to search
            
        Returns:
            Dictionary containing search results
        """
        base_path = Path(directory).expanduser()
        
        if not base_path.exists():
            return {'error': f'Directory not found: {directory}'}
        if not base_path.is_dir():
            return {'error': f'Path is not a directory: {directory}'}
        
        try:
            # Compile regex if it looks like a regex pattern
            is_regex = len(search_term) > 2 and search_term[0] == '/' and search_term[-1] == '/'
            search_re = None
            
            if is_regex:
                try:
                    search_re = re.compile(search_term[1:-1], 0 if case_sensitive else re.IGNORECASE)
                except re.error as e:
                    return {'error': f'Invalid regex pattern: {e}'}
            
            results = []
            match_count = 0
            
            for file_path in self._walk_directory(base_path, file_pattern, True, False, max_depth):
                if match_count >= max_matches:
                    break
                    
                if not self._is_text_file(file_path):
                    continue
                    
                file_matches = self._search_in_file(
                    file_path, search_term, search_re, 
                    case_sensitive, max_matches - match_count
                )
                
                if file_matches['matches']:
                    results.append({
                        'file': str(file_path),
                        'matches': file_matches['matches'],
                        'line_count': file_matches['line_count']
                    })
                    match_count += len(file_matches['matches'])
            
            return {
                'directory': str(base_path),
                'search_term': search_term,
                'total_matches': match_count,
                'files_searched': len(results),
                'results': results
            }
            
        except Exception as e:
            error_msg = f'Error searching content: {e}'
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    # Internal helper methods
    def _walk_directory(self, 
                       base_path: Path, 
                       pattern: str, 
                       recursive: bool,
                       include_dirs: bool,
                       max_depth: Optional[int]) -> Generator[Path, None, None]:
        """Walk a directory and yield matching files."""
        if max_depth is not None and max_depth < 0:
            return
            
        try:
            for item in base_path.iterdir():
                try:
                    if item.is_file() or (include_dirs and item.is_dir()):
                        if fnmatch.fnmatch(item.name, pattern):
                            yield item
                    
                    if recursive and item.is_dir() and (max_depth is None or max_depth > 0):
                        yield from self._walk_directory(
                            item, pattern, recursive, include_dirs, 
                            max_depth - 1 if max_depth is not None else None
                        )
                except (PermissionError, OSError) as e:
                    logger.warning(f'Error accessing {item}: {e}')
        except (PermissionError, OSError) as e:
            logger.warning(f'Error accessing directory {base_path}: {e}')
    
    def _search_in_file(self, 
                       file_path: Path, 
                       search_term: str, 
                       search_re: Optional[Pattern],
                       case_sensitive: bool,
                       max_matches: int) -> Dict[str, Any]:
        """Search for a term in a file."""
        matches = []
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_count = line_num
                    line = line.rstrip('\r\n')
                    
                    if search_re:
                        # Use regex search
                        if search_re.search(line):
                            matches.append({
                                'line': line_num,
                                'content': line,
                                'match': search_re.search(line).group(0)
                            })
                    else:
                        # Use simple string search
                        if not case_sensitive:
                            if search_term.lower() in line.lower():
                                matches.append({
                                    'line': line_num,
                                    'content': line,
                                    'match': search_term
                                })
                        else:
                            if search_term in line:
                                matches.append({
                                    'line': line_num,
                                    'content': line,
                                    'match': search_term
                                })
                    
                    if len(matches) >= max_matches:
                        break
                        
        except Exception as e:
            logger.error(f'Error searching in file {file_path}: {e}')
        
        return {
            'matches': matches,
            'line_count': line_count
        }
