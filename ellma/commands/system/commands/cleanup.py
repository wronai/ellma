"""
System cleanup command.

This module provides the `cleanup` command which performs system cleanup tasks.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import shutil
import tempfile
from pathlib import Path
import time
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from ..commands import BaseCommand, CommandResult
from ...utils import (
    cleanup_temp_files,
    cleanup_old_logs
)

class CleanupCommand(BaseCommand):
    """Perform system cleanup tasks."""
    
    def execute(self, 
               temp: bool = True, 
               logs: bool = False, 
               cache: bool = False,
               downloads: bool = False,
               trash: bool = False,
               older_than_days: int = 30,
               dry_run: bool = False,
               *args, **kwargs) -> CommandResult:
        """Execute the cleanup command.
        
        Args:
            temp: Clean temporary files.
            logs: Clean old log files.
            cache: Clean cache files.
            downloads: Clean old downloads.
            trash: Empty trash/recycle bin.
            older_than_days: Delete files older than this many days.
            dry_run: Show what would be deleted without actually deleting.
            
        Returns:
            CommandResult: Contains cleanup results.
        """
        try:
            results = {
                "start_time": datetime.now().isoformat(),
                "dry_run": dry_run,
                "tasks": {}
            }
            
            # Create progress bar
            total_tasks = sum([temp, logs, cache, downloads, trash])
            if total_tasks == 0:
                self.console.print("[yellow]No cleanup tasks selected. Use --help to see available options.[/yellow]")
                return CommandResult(success=True, data=results)
            
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TimeElapsedColumn(),
                console=self.console,
                expand=True
            ) as progress:
                task = progress.add_task("Cleaning up...", total=total_tasks)
                
                # Clean temporary files
                if temp:
                    progress.update(task, description="[cyan]Cleaning temporary files...")
                    results["tasks"]["temp_files"] = self._clean_temp_files(older_than_days, dry_run)
                    progress.update(task, advance=1)
                
                # Clean log files
                if logs:
                    progress.update(task, description="[blue]Cleaning log files...")
                    results["tasks"]["log_files"] = self._clean_log_files(older_than_days, dry_run)
                    progress.update(task, advance=1)
                
                # Clean cache files
                if cache:
                    progress.update(task, description="[magenta]Cleaning cache files...")
                    results["tasks"]["cache_files"] = self._clean_cache_files(older_than_days, dry_run)
                    progress.update(task, advance=1)
                
                # Clean downloads
                if downloads:
                    progress.update(task, description="[yellow]Cleaning downloads...")
                    results["tasks"]["downloads"] = self._clean_downloads(older_than_days, dry_run)
                    progress.update(task, advance=1)
                
                # Empty trash
                if trash:
                    progress.update(task, description="[red]Emptying trash...")
                    results["tasks"]["trash"] = self._empty_trash(dry_run)
                    progress.update(task, advance=1)
            
            # Calculate totals
            results["end_time"] = datetime.now().isoformat()
            results["total_freed"] = sum(
                task.get("freed", 0) 
                for task in results["tasks"].values()
            )
            results["total_files"] = sum(
                task.get("deleted", 0) 
                for task in results["tasks"].values()
            )
            
            # Display summary
            self._display_summary(results)
            
            return CommandResult(success=True, data=results)
            
        except Exception as e:
            error_msg = f"Failed to perform cleanup: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _clean_temp_files(self, older_than_days: int, dry_run: bool) -> Dict[str, Any]:
        """Clean temporary files.
        
        Args:
            older_than_days: Delete files older than this many days.
            dry_run: If True, don't actually delete anything.
            
        Returns:
            Dictionary with cleanup results.
        """
        result = {
            "type": "temp_files",
            "deleted": 0,
            "failed": 0,
            "freed": 0,
            "paths": []
        }
        
        # Common temporary directories
        temp_dirs = [
            "/tmp",
            "/var/tmp",
            tempfile.gettempdir(),
            os.path.expanduser("~/tmp"),
            os.path.expanduser("~/.cache"),
            "/private/var/folders",  # macOS
            "/private/var/tmp",      # macOS
        ]
        
        # Add Windows temp directories if on Windows
        if os.name == 'nt':
            temp_dirs.extend([
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                os.environ.get('LOCALAPPDATA', '') + '\\Temp',
                'C:\\Windows\\Temp',
                'C:\\Temp'
            ])
        
        # Calculate cutoff time
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        
        for temp_dir in temp_dirs:
            if not temp_dir or not os.path.exists(temp_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    # Skip system directories
                    if any(skip in root.lower() for skip in ['system32', 'winsxs', 'installer', 'driverstore']):
                        continue
                        
                    # Process files
                    for name in files:
                        try:
                            file_path = os.path.join(root, name)
                            
                            # Skip special files
                            if os.path.islink(file_path) or not os.path.isfile(file_path):
                                continue
                            
                            # Check file age
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > cutoff_time:
                                continue
                            
                            # Get file size
                            file_size = os.path.getsize(file_path)
                            
                            if not dry_run:
                                try:
                                    os.unlink(file_path)
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                except Exception as e:
                                    result["failed"] += 1
                            else:
                                result["deleted"] += 1
                                result["freed"] += file_size
                                result["paths"].append(file_path)
                                
                        except (OSError, PermissionError) as e:
                            result["failed"] += 1
                            continue
                    
                    # Process directories (remove if empty)
                    if not dry_run:
                        try:
                            os.rmdir(root)
                        except OSError:
                            pass  # Directory not empty
                            
            except (OSError, PermissionError) as e:
                result["failed"] += 1
                continue
        
        return result
    
    def _clean_log_files(self, older_than_days: int, dry_run: bool) -> Dict[str, Any]:
        """Clean log files.
        
        Args:
            older_than_days: Delete files older than this many days.
            dry_run: If True, don't actually delete anything.
            
        Returns:
            Dictionary with cleanup results.
        """
        result = {
            "type": "log_files",
            "deleted": 0,
            "failed": 0,
            "freed": 0,
            "paths": []
        }
        
        # Common log directories
        log_dirs = [
            "/var/log",
            "/var/adm",
            "/var/cache",
            os.path.expanduser("~/.cache"),
            os.path.expanduser("~/.local/share/logs"),
            "/Library/Logs",  # macOS
            "/private/var/log",  # macOS
        ]
        
        # Add Windows log directories if on Windows
        if os.name == 'nt':
            log_dirs.extend([
                os.environ.get('WINDIR', '') + '\\Logs',
                os.environ.get('WINDIR', '') + '\\System32\\LogFiles',
                os.environ.get('LOCALAPPDATA', '') + '\\Temp',
                'C:\\Windows\\Logs',
                'C:\\Windows\\System32\\LogFiles',
                'C:\\Windows\\Temp',
            ])
        
        # Calculate cutoff time
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        
        for log_dir in log_dirs:
            if not log_dir or not os.path.exists(log_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(log_dir):
                    # Skip system directories
                    if any(skip in root.lower() for skip in ['system32', 'winsxs', 'installer', 'driverstore']):
                        continue
                        
                    for name in files:
                        # Only process log files
                        if not any(name.endswith(ext) for ext in ['.log', '.gz', '.zip', '.old', '.bak', '.1', '.2']):
                            continue
                            
                        try:
                            file_path = os.path.join(root, name)
                            
                            # Skip special files
                            if os.path.islink(file_path) or not os.path.isfile(file_path):
                                continue
                            
                            # Check file age
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > cutoff_time:
                                continue
                            
                            # Get file size
                            file_size = os.path.getsize(file_path)
                            
                            if not dry_run:
                                try:
                                    os.unlink(file_path)
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                except Exception as e:
                                    result["failed"] += 1
                            else:
                                result["deleted"] += 1
                                result["freed"] += file_size
                                result["paths"].append(file_path)
                                
                        except (OSError, PermissionError) as e:
                            result["failed"] += 1
                            continue
                            
            except (OSError, PermissionError) as e:
                result["failed"] += 1
                continue
        
        return result
    
    def _clean_cache_files(self, older_than_days: int, dry_run: bool) -> Dict[str, Any]:
        """Clean cache files.
        
        Args:
            older_than_days: Delete files older than this many days.
            dry_run: If True, don't actually delete anything.
            
        Returns:
            Dictionary with cleanup results.
        """
        result = {
            "type": "cache_files",
            "deleted": 0,
            "failed": 0,
            "freed": 0,
            "paths": []
        }
        
        # Common cache directories
        cache_dirs = [
            os.path.expanduser("~/.cache"),
            os.path.expanduser("~/.npm"),  # npm cache
            os.path.expanduser("~/.m2"),   # Maven cache
            os.path.expanduser("~/.gradle/caches"),  # Gradle cache
            "/Library/Caches",  # macOS system caches
            "/private/var/folders",  # macOS user caches
            "/var/cache",
            "/var/tmp",
        ]
        
        # Add Windows cache directories if on Windows
        if os.name == 'nt':
            cache_dirs.extend([
                os.environ.get('LOCALAPPDATA', '') + '\\Temp',
                os.environ.get('LOCALAPPDATA', '') + '\\Microsoft\\Windows\\INetCache',
                os.environ.get('LOCALAPPDATA', '') + '\\Microsoft\\Windows\\WER',
                os.environ.get('APPDATA', '') + '\\npm-cache',
                os.environ.get('USERPROFILE', '') + '\\AppData\\Local\\Temp',
                'C:\\Windows\\Temp',
                'C:\\Windows\\Prefetch',
            ])
        
        # Calculate cutoff time
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        
        for cache_dir in cache_dirs:
            if not cache_dir or not os.path.exists(cache_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(cache_dir):
                    # Skip system directories
                    if any(skip in root.lower() for skip in ['system32', 'winsxs', 'installer', 'driverstore']):
                        continue
                        
                    for name in files:
                        try:
                            file_path = os.path.join(root, name)
                            
                            # Skip special files
                            if os.path.islink(file_path) or not os.path.isfile(file_path):
                                continue
                            
                            # Check file age
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > cutoff_time:
                                continue
                            
                            # Get file size
                            file_size = os.path.getsize(file_path)
                            
                            if not dry_run:
                                try:
                                    os.unlink(file_path)
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                except Exception as e:
                                    result["failed"] += 1
                            else:
                                result["deleted"] += 1
                                result["freed"] += file_size
                                result["paths"].append(file_path)
                                
                        except (OSError, PermissionError) as e:
                            result["failed"] += 1
                            continue
                    
                    # Process directories (remove if empty)
                    if not dry_run:
                        try:
                            os.rmdir(root)
                        except OSError:
                            pass  # Directory not empty
                            
            except (OSError, PermissionError) as e:
                result["failed"] += 1
                continue
        
        return result
    
    def _clean_downloads(self, older_than_days: int, dry_run: bool) -> Dict[str, Any]:
        """Clean downloads directory.
        
        Args:
            older_than_days: Delete files older than this many days.
            dry_run: If True, don't actually delete anything.
            
        Returns:
            Dictionary with cleanup results.
        """
        result = {
            "type": "downloads",
            "deleted": 0,
            "failed": 0,
            "freed": 0,
            "paths": []
        }
        
        # Common downloads directories
        download_dirs = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/downloads"),
        ]
        
        # Add Windows downloads directory if on Windows
        if os.name == 'nt':
            download_dirs.append(os.path.join(os.environ['USERPROFILE'], 'Downloads'))
        
        # Calculate cutoff time
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        
        for dl_dir in download_dirs:
            if not dl_dir or not os.path.exists(dl_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(dl_dir):
                    for name in files:
                        try:
                            file_path = os.path.join(root, name)
                            
                            # Skip special files
                            if os.path.islink(file_path) or not os.path.isfile(file_path):
                                continue
                            
                            # Skip recent files
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > cutoff_time:
                                continue
                            
                            # Get file size
                            file_size = os.path.getsize(file_path)
                            
                            if not dry_run:
                                try:
                                    os.unlink(file_path)
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                except Exception as e:
                                    result["failed"] += 1
                            else:
                                result["deleted"] += 1
                                result["freed"] += file_size
                                result["paths"].append(file_path)
                                
                        except (OSError, PermissionError) as e:
                            result["failed"] += 1
                            continue
                    
                    # Process directories (remove if empty)
                    if not dry_run:
                        try:
                            os.rmdir(root)
                        except OSError:
                            pass  # Directory not empty
                            
            except (OSError, PermissionError) as e:
                result["failed"] += 1
                continue
        
        return result
    
    def _empty_trash(self, dry_run: bool) -> Dict[str, Any]:
        """Empty the trash/recycle bin.
        
        Args:
            dry_run: If True, don't actually delete anything.
            
        Returns:
            Dictionary with cleanup results.
        """
        result = {
            "type": "trash",
            "deleted": 0,
            "failed": 0,
            "freed": 0,
            "paths": []
        }
        
        # Platform-specific trash locations
        if os.name == 'nt':  # Windows
            try:
                from win32com.shell import shell, shellcon
                
                if not dry_run:
                    # This requires the pywin32 package
                    shell.SHFileOperation((
                        0,  # hwnd
                        shellcon.FO_DELETE,  # Operation
                        shell.SHGetFolderPath(0, shellcon.CSIDL_BITBUCKET, None, 0),  # Path
                        None,  # Files
                        shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_SILENT,
                        None,  # No progress
                        None   # No title
                    ))
                    
                    # We can't easily get the count/size of files in the recycle bin
                    result["deleted"] = 1
                    result["paths"].append("Recycle Bin")
                else:
                    result["deleted"] = 1
                    result["paths"].append("Recycle Bin (dry run)")
                    
            except ImportError:
                result["failed"] = 1
                result["paths"].append("Failed to empty Recycle Bin: pywin32 not installed")
                
        elif os.uname().sysname == 'Darwin':  # macOS
            trash_dirs = [
                os.path.expanduser('~/.Trash'),
                '/private/var/root/.Trash'
            ]
            
            for trash_dir in trash_dirs:
                if not os.path.exists(trash_dir):
                    continue
                    
                try:
                    for root, dirs, files in os.walk(trash_dir, topdown=False):
                        for name in files:
                            try:
                                file_path = os.path.join(root, name)
                                
                                # Skip special files
                                if os.path.islink(file_path) or not os.path.isfile(file_path):
                                    continue
                                
                                # Get file size
                                file_size = os.path.getsize(file_path)
                                
                                if not dry_run:
                                    try:
                                        os.unlink(file_path)
                                        result["deleted"] += 1
                                        result["freed"] += file_size
                                        result["paths"].append(file_path)
                                    except Exception as e:
                                        result["failed"] += 1
                                else:
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                    
                            except (OSError, PermissionError) as e:
                                result["failed"] += 1
                                continue
                        
                        # Remove empty directories
                        if not dry_run:
                            try:
                                os.rmdir(root)
                            except OSError:
                                pass  # Directory not empty
                                
                except (OSError, PermissionError) as e:
                    result["failed"] += 1
                    continue
                    
        else:  # Linux and other Unix-like
            trash_dirs = [
                os.path.expanduser('~/.local/share/Trash'),
                os.path.expanduser('~/.trash'),
                '/root/.local/share/Trash',
                '/root/.trash'
            ]
            
            for trash_dir in trash_dirs:
                if not os.path.exists(trash_dir):
                    continue
                    
                # For freedesktop.org trash specification
                files_dir = os.path.join(trash_dir, 'files')
                info_dir = os.path.join(trash_dir, 'info')
                
                if os.path.exists(files_dir) and os.path.exists(info_dir):
                    try:
                        for name in os.listdir(files_dir):
                            try:
                                file_path = os.path.join(files_dir, name)
                                info_path = os.path.join(info_dir, name + '.trashinfo')
                                
                                # Skip special files
                                if not os.path.isfile(file_path) and not os.path.isdir(file_path):
                                    continue
                                
                                # Get file size
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                else:
                                    file_size = sum(
                                        os.path.getsize(os.path.join(dirpath, filename))
                                        for dirpath, _, filenames in os.walk(file_path)
                                        for filename in filenames
                                    )
                                
                                if not dry_run:
                                    try:
                                        if os.path.isfile(file_path):
                                            os.unlink(file_path)
                                        else:
                                            shutil.rmtree(file_path)
                                        
                                        # Remove info file if it exists
                                        if os.path.exists(info_path):
                                            os.unlink(info_path)
                                            
                                        result["deleted"] += 1
                                        result["freed"] += file_size
                                        result["paths"].append(file_path)
                                    except Exception as e:
                                        result["failed"] += 1
                                else:
                                    result["deleted"] += 1
                                    result["freed"] += file_size
                                    result["paths"].append(file_path)
                                    
                            except (OSError, PermissionError) as e:
                                result["failed"] += 1
                                continue
                                
                    except (OSError, PermissionError) as e:
                        result["failed"] += 1
                        continue
                else:
                    # Simple recursive delete for non-standard trash directories
                    try:
                        for root, dirs, files in os.walk(trash_dir, topdown=False):
                            for name in files:
                                try:
                                    file_path = os.path.join(root, name)
                                    
                                    # Skip special files
                                    if not os.path.isfile(file_path):
                                        continue
                                    
                                    # Get file size
                                    file_size = os.path.getsize(file_path)
                                    
                                    if not dry_run:
                                        try:
                                            os.unlink(file_path)
                                            result["deleted"] += 1
                                            result["freed"] += file_size
                                            result["paths"].append(file_path)
                                        except Exception as e:
                                            result["failed"] += 1
                                    else:
                                        result["deleted"] += 1
                                        result["freed"] += file_size
                                        result["paths"].append(file_path)
                                        
                                except (OSError, PermissionError) as e:
                                    result["failed"] += 1
                                    continue
                            
                            # Remove empty directories
                            if not dry_run:
                                try:
                                    os.rmdir(root)
                                except OSError:
                                    pass  # Directory not empty
                                    
                    except (OSError, PermissionError) as e:
                        result["failed"] += 1
                        continue
        
        return result
    
    def _display_summary(self, results: Dict[str, Any]) -> None:
        """Display a summary of the cleanup results.
        
        Args:
            results: Dictionary containing cleanup results.
        """
        if results.get("dry_run"):
            self.console.print("\n[bold yellow]DRY RUN: No files were actually deleted[/bold yellow]\n")
        
        # Create summary table
        table = Table(
            title="Cleanup Summary",
            show_header=True,
            header_style="bold magenta",
            box=None
        )
        
        table.add_column("Task", style="cyan")
        table.add_column("Files Deleted", justify="right")
        table.add_column("Space Freed", justify="right")
        table.add_column("Failed", justify="right")
        
        # Add rows for each task
        for task_name, task in results.get("tasks", {}).items():
            table.add_row(
                task_name.replace("_", " ").title(),
                str(task.get("deleted", 0)),
                self._format_bytes(task.get("freed", 0)),
                str(task.get("failed", 0))
            )
        
        # Add total row
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{results.get('total_files', 0)}[/bold]",
            f"[bold]{self._format_bytes(results.get('total_freed', 0))}[/bold]",
            f"[bold]{sum(t.get('failed', 0) for t in results.get('tasks', {}).values())}"
        )
        
        self.console.print(table)
        
        # Show warning if there were failures
        if any(task.get("failed", 0) > 0 for task in results.get("tasks", {}).values()):
            self.console.print("\n[bold yellow]Warning: Some operations failed. You may need to run as administrator/root.[/bold yellow]")
        
        # Show total space freed
        self.console.print(f"\n[bold]Total space freed:[/bold] {self._format_bytes(results.get('total_freed', 0))}")

def execute(temp: bool = True, logs: bool = False, cache: bool = False, 
           downloads: bool = False, trash: bool = False, 
           older_than_days: int = 30, dry_run: bool = False, 
           *args, **kwargs) -> CommandResult:
    """Execute the cleanup command.
    
    This is the entry point for the cleanup command.
    
    Args:
        temp: Clean temporary files.
        logs: Clean old log files.
        cache: Clean cache files.
        downloads: Clean old downloads.
        trash: Empty trash/recycle bin.
        older_than_days: Delete files older than this many days.
        dry_run: Show what would be deleted without actually deleting.
        
    Returns:
        CommandResult: The result of the command execution.
    """
    return CleanupCommand().execute(
        temp=temp,
        logs=logs,
        cache=cache,
        downloads=downloads,
        trash=trash,
        older_than_days=older_than_days,
        dry_run=dry_run,
        *args,
        **kwargs
    )
