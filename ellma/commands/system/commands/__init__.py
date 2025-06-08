"""
System command implementations.

This package contains the implementation of individual system commands.
Each command is implemented as a separate module with a single `execute` function.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
import os
import time
import psutil
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import from our refactored modules
from ..core import (
    get_platform_info,
    get_hardware_info,
    get_resource_usage,
    get_network_info,
    get_storage_info,
    get_process_info,
    get_services_info,
    get_security_status,
    get_load_average,
    get_uptime
)

from ..utils import (
    parse_log_line,
    get_log_files,
    read_logs,
    get_level_style,
    get_numeric_log_level,
    cleanup_temp_files,
    cleanup_old_logs,
    calculate_health_score
)

# Configure logging
import logging
logger = logging.getLogger(__name__)

class CommandError(Exception):
    """Base exception for command-related errors."""
    pass

class CommandResult:
    """Container for command execution results."""
    
    def __init__(self, success: bool = True, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandResult':
        """Create a CommandResult from a dictionary."""
        return cls(
            success=data.get("success", True),
            data=data.get("data"),
            error=data.get("error")
        )

class BaseCommand:
    """Base class for all system commands."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the command.
        
        Args:
            console: Rich console instance for output. If not provided, a new one will be created.
        """
        self.console = console or Console()
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """Execute the command.
        
        Subclasses should override this method to implement command-specific logic.
        
        Returns:
            CommandResult: The result of the command execution.
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def _display_table(self, title: str, columns: List[str], rows: List[List[Any]]) -> None:
        """Display tabular data.
        
        Args:
            title: Table title
            columns: List of column names
            rows: List of rows (each row is a list of cell values)
        """
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Add columns
        for col in columns:
            table.add_column(col)
            
        # Add rows
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
            
        self.console.print(table)
    
    def _display_key_value(self, title: str, data: Dict[str, Any], columns: int = 2) -> None:
        """Display key-value pairs in a grid.
        
        Args:
            title: Section title
            data: Dictionary of key-value pairs
            columns: Number of columns in the grid
        """
        self.console.print(f"[bold]{title}[/bold]")
        
        items = list(data.items())
        rows = [items[i:i + columns] for i in range(0, len(items), columns)]
        
        for row in rows:
            row_text = []
            for key, value in row:
                row_text.append(f"[cyan]{key}:[/cyan] {value}")
            self.console.print("  ".join(row_text))
        
        self.console.print()  # Add some space after the section
    
    def _format_bytes(self, size: int) -> str:
        """Format bytes into a human-readable string.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB, TB)
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _format_timedelta(self, td: timedelta) -> str:
        """Format a timedelta into a human-readable string.
        
        Args:
            td: Timedelta to format
            
        Returns:
            Formatted string (e.g., "2 days, 3:45:30")
        """
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
