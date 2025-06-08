"""
ELLMa File Commands - File and Directory Operations

This module provides comprehensive file and directory operations including
reading, writing, analysis, searching, and batch processing capabilities.

Note: This module has been refactored into smaller, more maintainable modules.
The original interface is maintained for backward compatibility, but new code
should import from the specific submodules directly.
"""

import warnings

# Import the new implementation
from .files import FileCommands as _FileCommands

# Issue deprecation warning
warnings.warn(
    "The files module has been refactored. Import from ellma.commands.files instead.",
    DeprecationWarning,
    stacklevel=2
)

# Maintain the same interface for backward compatibility
FileCommands = _FileCommands

# The rest of the original file has been moved to the files/ directory.
# This is maintained for backward compatibility only.
                        result['lines'] = len(lines)
                        result['truncated'] = i >= max_lines - 1
                    else:
                        content = f.read()
                        result['content'] = content
                        result['lines'] = content.count('\n') + 1
                        result['truncated'] = False
            else:
                result['content'] = f'Binary file ({file_size} bytes)'
                result['binary_preview'] = self._get_binary_preview(path)

            return result

        except UnicodeDecodeError:
            return {'error': f'Cannot decode file with encoding: {encoding}'}
        except PermissionError:
            return {'error': f'Permission denied: {file_path}'}
        except Exception as e:
            return {'error': f'Error reading file: {e}'}

    @validate_args(str, str)
    @log_execution
    def write(self, file_path: str, content: str, encoding: str = 'utf-8',
              backup: bool = True, create_dirs: bool = True) -> Dict[str, Any]:
        """
        Write content to file

        Args:
            file_path: Path to file
            content: Content to write
            encoding: File encoding
            backup: Create backup if file exists
            create_dirs: Create parent directories if needed

        Returns:
            Write operation result
        """
        path = Path(file_path).expanduser()

        # Create parent directories if needed
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        backup_path = None
        if backup and path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = path.with_suffix(f'.backup_{timestamp}{path.suffix}')
            try:
                shutil.copy2(path, backup_path)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                backup_path = None

        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            return {
                'path': str(path),
                'bytes_written': len(content.encode(encoding)),
                'lines_written': content.count('\n') + 1,
                'backup_created': str(backup_path) if backup_path else None,
                'timestamp': datetime.now().isoformat()
            }

        except PermissionError:
            return {'error': f'Permission denied: {file_path}'}
        except Exception as e:
            return {'error': f'Error writing file: {e}'}

    @validate_args(str, str)
    @log_execution
    def append(self, file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Append content to file

        Args:
            file_path: Path to file
            content: Content to append
            encoding: File encoding

        Returns:
            Append operation result
        """
        path = Path(file_path).expanduser()

        try:
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)

            return {
                'path': str(path),
                'bytes_appended': len(content.encode(encoding)),
                'lines_appended': content.count('\n'),
                'timestamp': datetime.now().isoformat()
            }

        except PermissionError:
            return {'error': f'Permission denied: {file_path}'}
        except Exception as e:
            return {'error': f'Error appending to file: {e}'}

    @validate_args(str)
    @log_execution
    def analyze(self, path: str, pattern: Optional[str] = None,
                recursive: bool = True, include_content: bool = False) -> Dict[str, Any]:
        """
        Analyze file or directory

        Args:
            path: Path to analyze
            pattern: Pattern to search for in content
            recursive: Recursively analyze directories
            include_content: Include file content in analysis

        Returns:
            Analysis results
        """
        target_path = Path(path).expanduser()

        if not target_path.exists():
            return {'error': f'Path not found: {path}'}

        if target_path.is_file():
            return self._analyze_file(target_path, pattern, include_content)
        elif target_path.is_dir():
            return self._analyze_directory(target_path, pattern, recursive, include_content)
        else:
            return {'error': f'Unsupported path type: {path}'}

    @validate_args(str, str)
    @log_execution
    def search(self, directory: str, pattern: str, file_pattern: str = "*",
               case_sensitive: bool = False, include_binary: bool = False) -> List[Dict[str, Any]]:
        """
        Search for pattern in files

        Args:
            directory: Directory to search in
            pattern: Text pattern to search for
            file_pattern: File name pattern (glob style)
            case_sensitive: Case sensitive search
            include_binary: Include binary files in search

        Returns:
            List of matches
        """
        search_dir = Path(directory).expanduser()

        if not search_dir.exists() or not search_dir.is_dir():
            return [{'error': f'Directory not found: {directory}'}]

        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        regex_pattern = re.compile(pattern, flags)

        try:
            for file_path in search_dir.rglob(file_pattern):
                if not file_path.is_file():
                    continue

                # Skip binary files unless requested
                if not include_binary and not self._is_text_file(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            match_obj = regex_pattern.search(line)
                            if match_obj:
                                matches.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'match': match_obj.group(),
                                    'start': match_obj.start(),
                                    'end': match_obj.end()
                                })

                                # Limit matches per file to prevent memory issues
                                if len([m for m in matches if m['file'] == str(file_path)]) > 100:
                                    break

                except (UnicodeDecodeError, PermissionError):
                    continue

        except Exception as e:
            return [{'error': f'Search failed: {e}'}]

        return matches

    @validate_args(str, str)
    @log_execution
    def copy(self, source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Copy file or directory

        Args:
            source: Source path
            destination: Destination path
            overwrite: Overwrite existing files

        Returns:
            Copy operation result
        """
        src_path = Path(source).expanduser()
        dst_path = Path(destination).expanduser()

        if not src_path.exists():
            return {'error': f'Source not found: {source}'}

        if dst_path.exists() and not overwrite:
            return {'error': f'Destination exists: {destination}'}

        try:
            if src_path.is_file():
                shutil.copy2(src_path, dst_path)
                operation = 'file_copy'
            elif src_path.is_dir():
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                operation = 'directory_copy'
            else:
                return {'error': f'Unsupported source type: {source}'}

            return {
                'operation': operation,
                'source': str(src_path),
                'destination': str(dst_path),
                'size': self._get_path_size(dst_path),
                'timestamp': datetime.now().isoformat()
            }

        except PermissionError:
            return {'error': f'Permission denied'}
        except Exception as e:
            return {'error': f'Copy failed: {e}'}

    @validate_args(str, str)
    @log_execution
    def move(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move file or directory

        Args:
            source: Source path
            destination: Destination path

        Returns:
            Move operation result
        """
        src_path = Path(source).expanduser()
        dst_path = Path(destination).expanduser()

        if not src_path.exists():
            return {'error': f'Source not found: {source}'}

        if dst_path.exists():
            return {'error': f'Destination exists: {destination}'}

        try:
            shutil.move(str(src_path), str(dst_path))

            return {
                'operation': 'move',
                'source': str(src_path),
                'destination': str(dst_path),
                'timestamp': datetime.now().isoformat()
            }

        except PermissionError:
            return {'error': f'Permission denied'}
        except Exception as e:
            return {'error': f'Move failed: {e}'}

    @validate_args(str)
    @log_execution
    def delete(self, path: str, confirm: bool = True) -> Dict[str, Any]:
        """
        Delete file or directory

        Args:
            path: Path to delete
            confirm: Require confirmation for deletion

        Returns:
            Delete operation result
        """
        target_path = Path(path).expanduser()

        if not target_path.exists():
            return {'error': f'Path not found: {path}'}

        # Safety check for important directories
        dangerous_paths = [Path.home(), Path('/'), Path('/usr'), Path('/etc')]
        if any(target_path.resolve() == dp.resolve() for dp in dangerous_paths):
            return {'error': f'Cannot delete system directory: {path}'}

        if confirm and not self._confirm_action(f"Delete {path}?"):
            return {'error': 'Operation cancelled by user'}

        try:
            if target_path.is_file():
                size = target_path.stat().st_size
                target_path.unlink()
                operation = 'file_delete'
            elif target_path.is_dir():
                size = self._get_path_size(target_path)
                shutil.rmtree(target_path)
                operation = 'directory_delete'
            else:
                return {'error': f'Unsupported path type: {path}'}

            return {
                'operation': operation,
                'path': str(target_path),
                'size_freed': size,
                'timestamp': datetime.now().isoformat()
            }

        except PermissionError:
            return {'error': f'Permission denied'}
        except Exception as e:
            return {'error': f'Delete failed: {e}'}

    @validate_args(str)
    @log_execution
    def list_directory(self, directory: str, recursive: bool = False,
                      show_hidden: bool = False, sort_by: str = 'name') -> List[Dict[str, Any]]:
        """
        List directory contents

        Args:
            directory: Directory to list
            recursive: Recursively list subdirectories
            show_hidden: Show hidden files
            sort_by: Sort by (name, size, modified, type)

        Returns:
            List of directory entries
        """
        dir_path = Path(directory).expanduser()

        if not dir_path.exists() or not dir_path.is_dir():
            return [{'error': f'Directory not found: {directory}'}]

        entries = []

        try:
            if recursive:
                pattern = "**/*" if show_hidden else "**/[!.]*"
                paths = dir_path.glob(pattern)
            else:
                pattern = "*" if show_hidden else "[!.]*"
                paths = dir_path.glob(pattern)

            for path in paths:
                try:
                    stat_result = path.stat()
                    entry = {
                        'name': path.name,
                        'path': str(path),
                        'type': 'directory' if path.is_dir() else 'file',
                        'size': stat_result.st_size if path.is_file() else self._get_path_size(path),
                        'modified': datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
                        'permissions': oct(stat_result.st_mode)[-3:],
                        'extension': path.suffix.lower() if path.is_file() else '',
                        'is_hidden': path.name.startswith('.')
                    }

                    if path.is_file():
                        entry['mime_type'] = mimetypes.guess_type(str(path))[0]
                        entry['is_text'] = self._is_text_file(path)

                    entries.append(entry)

                except (PermissionError, OSError):
                    continue

            # Sort entries
            if sort_by == 'size':
                entries.sort(key=lambda x: x['size'], reverse=True)
            elif sort_by == 'modified':
                entries.sort(key=lambda x: x['modified'], reverse=True)
            elif sort_by == 'type':
                entries.sort(key=lambda x: (x['type'], x['name']))
            else:  # name
                entries.sort(key=lambda x: x['name'])

        except PermissionError:
            return [{'error': f'Permission denied: {directory}'}]
        except Exception as e:
            return [{'error': f'List failed: {e}'}]

        return entries

    @validate_args(str)
    @log_execution
    def find_duplicates(self, directory: str, by_content: bool = True) -> List[Dict[str, Any]]:
        """
        Find duplicate files

        Args:
            directory: Directory to search
            by_content: Compare by content hash (vs size+name)

        Returns:
            List of duplicate file groups
        """
        dir_path = Path(directory).expanduser()

        if not dir_path.exists() or not dir_path.is_dir():
            return [{'error': f'Directory not found: {directory}'}]

        file_groups = {}
        duplicates = []

        try:
            for file_path in dir_path.rglob('*'):
                if not file_path.is_file():
                    continue

                try:
                    stat_result = file_path.stat()

                    if by_content:
                        key = self._calculate_hash(file_path)
                    else:
                        key = f"{file_path.name}_{stat_result.st_size}"

                    if key not in file_groups:
                        file_groups[key] = []

                    file_groups[key].append({
                        'path': str(file_path),
                        'size': stat_result.st_size,
                        'modified': datetime.fromtimestamp(stat_result.st_mtime).isoformat()
                    })

                except (PermissionError, OSError):
                    continue

            # Find groups with multiple files
            for key, files in file_groups.items():
                if len(files) > 1:
                    total_size = sum(f['size'] for f in files)
                    wasted_space = total_size - files[0]['size']  # Space that could be freed

                    duplicates.append({
                        'hash' if by_content else 'name_size': key,
                        'count': len(files),
                        'files': files,
                        'total_size': total_size,
                        'wasted_space': wasted_space
                    })

            # Sort by wasted space (most significant first)
            duplicates.sort(key=lambda x: x['wasted_space'], reverse=True)

        except Exception as e:
            return [{'error': f'Duplicate search failed: {e}'}]

        return duplicates

    @validate_args(str)
    @log_execution
    def cleanup_directory(self, directory: str, older_than_days: int = 30,
                         file_patterns: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """
        Cleanup old or temporary files

        Args:
            directory: Directory to clean
            older_than_days: Delete files older than this many days
            file_patterns: File patterns to delete (e.g., ['*.tmp', '*.log'])
            dry_run: Show what would be deleted without actually deleting

        Returns:
            Cleanup results
        """
        dir_path = Path(directory).expanduser()

        if not dir_path.exists() or not dir_path.is_dir():
            return {'error': f'Directory not found: {directory}'}

        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        patterns = file_patterns or ['*.tmp', '*.log', '*.bak', '*~']

        files_to_delete = []
        total_size = 0

        try:
            for pattern in patterns:
                for file_path in dir_path.rglob(pattern):
                    if not file_path.is_file():
                        continue

                    try:
                        stat_result = file_path.stat()
                        file_date = datetime.fromtimestamp(stat_result.st_mtime)

                        if file_date < cutoff_date:
                            files_to_delete.append({
                                'path': str(file_path),
                                'size': stat_result.st_size,
                                'modified': file_date.isoformat(),
                                'pattern': pattern
                            })
                            total_size += stat_result.st_size

                    except (PermissionError, OSError):
                        continue

            result = {
                'directory': str(dir_path),
                'files_found': len(files_to_delete),
                'total_size': total_size,
                'dry_run': dry_run,
                'files': files_to_delete[:100]  # Limit to first 100 for display
            }

            if not dry_run and files_to_delete:
                deleted_count = 0
                deleted_size = 0

                for file_info in files_to_delete:
                    try:
                        file_path = Path(file_info['path'])
                        file_path.unlink()
                        deleted_count += 1
                        deleted_size += file_info['size']
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_info['path']}: {e}")

                result.update({
                    'deleted_count': deleted_count,
                    'deleted_size': deleted_size,
                    'failed_count': len(files_to_delete) - deleted_count
                })

        except Exception as e:
            return {'error': f'Cleanup failed: {e}'}

        return result

    @validate_args(str)
    @log_execution
    def watch(self, path: str, callback: Optional[callable] = None,
             recursive: bool = True, interval: float = 1.0) -> Dict[str, Any]:
        """
        Watch file or directory for changes

        Args:
            path: Path to watch
            callback: Callback function for changes
            recursive: Watch subdirectories
            interval: Check interval in seconds

        Returns:
            Watch operation result
        """
        watch_path = Path(path).expanduser()

        if not watch_path.exists():
            return {'error': f'Path not found: {path}'}

        # This is a simplified implementation
        # In production, you'd use a proper file watching library like watchdog

        try:
            import time

            initial_state = self._get_directory_state(watch_path, recursive)
            start_time = datetime.now()
            changes = []

            self.console.print(f"Watching {path} for changes... (Press Ctrl+C to stop)")

            while True:
                time.sleep(interval)
                current_state = self._get_directory_state(watch_path, recursive)

                # Detect changes
                file_changes = self._detect_changes(initial_state, current_state)

                if file_changes:
                    changes.extend(file_changes)

                    for change in file_changes:
                        self.console.print(f"Change detected: {change}")

                        if callback:
                            try:
                                callback(change)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

                    initial_state = current_state

        except KeyboardInterrupt:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                'path': str(watch_path),
                'duration': duration,
                'changes_detected': len(changes),
                'changes': changes,
                'status': 'stopped_by_user'
            }
        except Exception as e:
            return {'error': f'Watch failed: {e}'}

    # Helper methods

    def _is_text_file(self, path: Path) -> bool:
        """Check if file is likely a text file"""
        if path.suffix.lower() in self.text_extensions:
            return True

        if path.suffix.lower() in self.binary_extensions:
            return False

        # Try to read a small sample
        try:
            with open(path, 'rb') as f:
                sample = f.read(1024)

            # Check for null bytes (common in binary files)
            if b'\x00' in sample:
                return False

            # Try to decode as UTF-8
            try:
                sample.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False

        except Exception:
            return False

    def _calculate_hash(self, path: Path, algorithm: str = 'sha256') -> str:
        """Calculate hash of file"""
        hash_obj = hashlib.new(algorithm)

        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return "unknown"

    def _get_binary_preview(self, path: Path) -> str:
        """Get preview of binary file"""
        try:
            with open(path, 'rb') as f:
                sample = f.read(64)

            # Convert to hex representation
            hex_preview = ' '.join(f'{b:02x}' for b in sample)
            return f"Binary preview: {hex_preview}"
        except Exception:
            return "Binary file (preview unavailable)"

    def _get_path_size(self, path: Path) -> int:
        """Get total size of path (file or directory)"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total_size = 0
            try:
                for item in path.rglob('*'):
                    if item.is_file():
                        try:
                            total_size += item.stat().st_size
                        except (PermissionError, OSError):
                            continue
            except Exception:
                pass
            return total_size
        return 0

    def _analyze_file(self, file_path: Path, pattern: Optional[str], include_content: bool) -> Dict[str, Any]:
        """Analyze a single file"""
        try:
            stat_result = file_path.stat()
            is_text = self._is_text_file(file_path)

            analysis = {
                'path': str(file_path),
                'type': 'file',
                'size': stat_result.st_size,
                'is_text': is_text,
                'extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'created': datetime.fromtimestamp(stat_result.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
                'permissions': oct(stat_result.st_mode)[-3:],
                'hash': self._calculate_hash(file_path),
                'lines': 0,
                'words': 0,
                'characters': 0
            }

            if is_text and stat_result.st_size < self.max_file_size:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    analysis['lines'] = content.count('\n') + 1
                    analysis['words'] = len(content.split())
                    analysis['characters'] = len(content)

                    if pattern:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        analysis['pattern_matches'] = len(matches)
                        analysis['matches'] = matches[:10]  # First 10 matches

                    if include_content:
                        analysis['content'] = content

                except Exception as e:
                    analysis['error'] = f"Failed to read content: {e}"

            return analysis

        except Exception as e:
            return {'error': f'Analysis failed: {e}'}

    def _analyze_directory(self, dir_path: Path, pattern: Optional[str],
                          recursive: bool, include_content: bool) -> Dict[str, Any]:
        """Analyze a directory"""
        try:
            analysis = {
                'path': str(dir_path),
                'type': 'directory',
                'total_files': 0,
                'total_directories': 0,
                'total_size': 0,
                'file_types': {},
                'largest_files': [],
                'pattern_matches': 0 if pattern else None,
                'files': []
            }

            files_by_size = []

            pattern_regex = re.compile(pattern, re.IGNORECASE) if pattern else None

            iterator = dir_path.rglob('*') if recursive else dir_path.iterdir()

            for item in iterator:
                try:
                    if item.is_file():
                        analysis['total_files'] += 1
                        size = item.stat().st_size
                        analysis['total_size'] += size

                        # Track file types
                        ext = item.suffix.lower() or 'no_extension'
                        analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1

                        # Track largest files
                        files_by_size.append((size, str(item)))

                        # Search for pattern if specified
                        if pattern_regex and self._is_text_file(item):
                            try:
                                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read(10000)  # Read first 10KB only
                                    matches = len(pattern_regex.findall(content))
                                    if matches > 0:
                                        analysis['pattern_matches'] += matches
                                        analysis['files'].append({
                                            'path': str(item),
                                            'matches': matches
                                        })
                            except Exception:
                                continue

                    elif item.is_dir():
                        analysis['total_directories'] += 1

                except (PermissionError, OSError):
                    continue

            # Get top 10 largest files
            files_by_size.sort(reverse=True)
            analysis['largest_files'] = [
                {'path': path, 'size': size}
                for size, path in files_by_size[:10]
            ]

            return analysis

        except Exception as e:
            return {'error': f'Directory analysis failed: {e}'}

    def _get_directory_state(self, path: Path, recursive: bool = True) -> Dict[str, Dict]:
        """Get current state of directory for change detection"""
        state = {}

        try:
            iterator = path.rglob('*') if recursive else path.iterdir()

            for item in iterator:
                try:
                    if item.is_file():
                        stat_result = item.stat()
                        state[str(item)] = {
                            'size': stat_result.st_size,
                            'mtime': stat_result.st_mtime,
                            'type': 'file'
                        }
                    elif item.is_dir():
                        stat_result = item.stat()
                        state[str(item)] = {
                            'mtime': stat_result.st_mtime,
                            'type': 'directory'
                        }
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

        return state

    def _detect_changes(self, old_state: Dict, new_state: Dict) -> List[Dict]:
        """Detect changes between two directory states"""
        changes = []

        # Find new files/directories
        for path in new_state:
            if path not in old_state:
                changes.append({
                    'type': 'created',
                    'path': path,
                    'item_type': new_state[path]['type'],
                    'timestamp': datetime.now().isoformat()
                })

        # Find deleted files/directories
        for path in old_state:
            if path not in new_state:
                changes.append({
                    'type': 'deleted',
                    'path': path,
                    'item_type': old_state[path]['type'],
                    'timestamp': datetime.now().isoformat()
                })

        # Find modified files
        for path in old_state:
            if path in new_state:
                old_item = old_state[path]
                new_item = new_state[path]

                if old_item['type'] == 'file' and new_item['type'] == 'file':
                    if (old_item['size'] != new_item['size'] or
                        old_item['mtime'] != new_item['mtime']):
                        changes.append({
                            'type': 'modified',
                            'path': path,
                            'item_type': 'file',
                            'old_size': old_item['size'],
                            'new_size': new_item['size'],
                            'timestamp': datetime.now().isoformat()
                        })

        return changes

    @validate_args(str)
    @log_execution
    def compress(self, path: str, archive_path: Optional[str] = None,
                format: str = 'zip') -> Dict[str, Any]:
        """
        Compress file or directory

        Args:
            path: Path to compress
            archive_path: Output archive path
            format: Archive format (zip, tar, tar.gz, tar.bz2)

        Returns:
            Compression result
        """
        source_path = Path(path).expanduser()

        if not source_path.exists():
            return {'error': f'Path not found: {path}'}

        if archive_path is None:
            archive_path = f"{source_path.name}.{format}"

        archive_path = Path(archive_path).expanduser()

        try:
            if format == 'zip':
                import zipfile

                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if source_path.is_file():
                        zipf.write(source_path, source_path.name)
                    else:
                        for file_path in source_path.rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(source_path.parent)
                                zipf.write(file_path, arcname)

            elif format in ['tar', 'tar.gz', 'tar.bz2']:
                import tarfile

                mode_map = {
                    'tar': 'w',
                    'tar.gz': 'w:gz',
                    'tar.bz2': 'w:bz2'
                }

                with tarfile.open(archive_path, mode_map[format]) as tar:
                    tar.add(source_path, arcname=source_path.name)

            else:
                return {'error': f'Unsupported format: {format}'}

            original_size = self._get_path_size(source_path)
            compressed_size = archive_path.stat().st_size
            compression_ratio = compressed_size / original_size if original_size > 0 else 0

            return {
                'operation': 'compress',
                'source': str(source_path),
                'archive': str(archive_path),
                'format': format,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'space_saved': original_size - compressed_size,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Compression failed: {e}'}

    @validate_args(str)
    @log_execution
    def extract(self, archive_path: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract archive

        Args:
            archive_path: Path to archive
            destination: Extraction destination

        Returns:
            Extraction result
        """
        archive_path = Path(archive_path).expanduser()

        if not archive_path.exists():
            return {'error': f'Archive not found: {archive_path}'}

        if destination is None:
            destination = archive_path.parent / archive_path.stem
        else:
            destination = Path(destination).expanduser()

        destination.mkdir(parents=True, exist_ok=True)

        try:
            if archive_path.suffix.lower() == '.zip':
                import zipfile

                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(destination)
                    extracted_files = zipf.namelist()

            elif archive_path.suffix.lower() in ['.tar', '.gz', '.bz2'] or '.tar.' in archive_path.name:
                import tarfile

                with tarfile.open(archive_path, 'r:*') as tar:
                    tar.extractall(destination)
                    extracted_files = tar.getnames()

            else:
                return {'error': f'Unsupported archive format: {archive_path.suffix}'}

            return {
                'operation': 'extract',
                'archive': str(archive_path),
                'destination': str(destination),
                'files_extracted': len(extracted_files),
                'extracted_files': extracted_files[:20],  # First 20 files
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Extraction failed: {e}'}

    @validate_args(str, str)
    @log_execution
    def replace_in_files(self, directory: str, pattern: str, replacement: str,
                        file_pattern: str = "*.txt", dry_run: bool = True) -> Dict[str, Any]:
        """
        Replace text pattern in multiple files

        Args:
            directory: Directory to search
            pattern: Text pattern to replace
            replacement: Replacement text
            file_pattern: File name pattern
            dry_run: Show what would be changed without making changes

        Returns:
            Replacement results
        """
        search_dir = Path(directory).expanduser()

        if not search_dir.exists() or not search_dir.is_dir():
            return {'error': f'Directory not found: {directory}'}

        results = {
            'directory': str(search_dir),
            'pattern': pattern,
            'replacement': replacement,
            'files_processed': 0,
            'replacements_made': 0,
            'dry_run': dry_run,
            'files': []
        }

        try:
            for file_path in search_dir.rglob(file_pattern):
                if not file_path.is_file() or not self._is_text_file(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Count matches
                    import re
                    matches = re.findall(pattern, content)

                    if matches:
                        new_content = re.sub(pattern, replacement, content)

                        file_result = {
                            'path': str(file_path),
                            'matches_found': len(matches),
                            'replacements': len(matches)
                        }

                        if not dry_run:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            file_result['status'] = 'modified'
                        else:
                            file_result['status'] = 'would_modify'

                        results['files'].append(file_result)
                        results['files_processed'] += 1
                        results['replacements_made'] += len(matches)

                except (UnicodeDecodeError, PermissionError) as e:
                    results['files'].append({
                        'path': str(file_path),
                        'error': str(e),
                        'status': 'error'
                    })

        except Exception as e:
            return {'error': f'Replace operation failed: {e}'}

        return results

    @validate_args(str)
    @log_execution
    def get_permissions(self, path: str) -> Dict[str, Any]:
        """
        Get detailed file permissions

        Args:
            path: Path to check

        Returns:
            Permission information
        """
        target_path = Path(path).expanduser()

        if not target_path.exists():
            return {'error': f'Path not found: {path}'}

        try:
            stat_result = target_path.stat()
            mode = stat_result.st_mode

            return {
                'path': str(target_path),
                'octal': oct(mode)[-3:],
                'symbolic': stat.filemode(mode),
                'owner': {
                    'read': bool(mode & stat.S_IRUSR),
                    'write': bool(mode & stat.S_IWUSR),
                    'execute': bool(mode & stat.S_IXUSR)
                },
                'group': {
                    'read': bool(mode & stat.S_IRGRP),
                    'write': bool(mode & stat.S_IWGRP),
                    'execute': bool(mode & stat.S_IXGRP)
                },
                'other': {
                    'read': bool(mode & stat.S_IROTH),
                    'write': bool(mode & stat.S_IWOTH),
                    'execute': bool(mode & stat.S_IXOTH)
                },
                'special': {
                    'sticky': bool(mode & stat.S_ISVTX),
                    'setgid': bool(mode & stat.S_ISGID),
                    'setuid': bool(mode & stat.S_ISUID)
                }
            }

        except Exception as e:
            return {'error': f'Failed to get permissions: {e}'}

    @validate_args(str, str)
    @log_execution
    def set_permissions(self, path: str, permissions: str) -> Dict[str, Any]:
        """
        Set file permissions

        Args:
            path: Path to modify
            permissions: Permissions in octal format (e.g., '755', '644')

        Returns:
            Permission change result
        """
        target_path = Path(path).expanduser()

        if not target_path.exists():
            return {'error': f'Path not found: {path}'}

        try:
            # Convert octal string to integer
            mode = int(permissions, 8)

            # Store old permissions
            old_mode = target_path.stat().st_mode
            old_permissions = oct(old_mode)[-3:]

            # Set new permissions
            target_path.chmod(mode)

            return {
                'path': str(target_path),
                'old_permissions': old_permissions,
                'new_permissions': permissions,
                'timestamp': datetime.now().isoformat()
            }

        except ValueError:
            return {'error': f'Invalid permissions format: {permissions}'}
        except PermissionError:
            return {'error': f'Permission denied to change permissions'}
        except Exception as e:
            return {'error': f'Failed to set permissions: {e}'}

if __name__ == "__main__":
    # Test the file commands
    import tempfile
    import sys

    # Mock agent for testing
    class MockAgent:
        def __init__(self):
            self.console = sys.stdout

    agent = MockAgent()
    file_commands = FileCommands(agent)

    # Test basic operations
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"

        # Test write
        result = file_commands.write(str(test_file), "Hello, World!\nThis is a test.")
        print("Write result:", result)

        # Test read
        result = file_commands.read(str(test_file))
        print("Read result:", result['content'] if 'content' in result else result)

        # Test list directory
        result = file_commands.list_directory(temp_dir)
        print("Directory listing:", len(result), "items")

        # Test analyze
        result = file_commands.analyze(str(test_file))
        print("File analysis:", {k: v for k, v in result.items() if k not in ['content']})

    print("File commands test completed")