"""
Error logging and self-improvement utilities for ELLMa.

This module provides functionality to log command errors to TODO/*.md files
for future self-improvement and automatic fixing.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, Callable

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound='ErrorLogger')


class ErrorLogger:
    """
    Handles logging of command errors to TODO/*.md files for future self-improvement.
    """
    
    def __init__(self, todo_dir: str = "TODO"):
        """
        Initialize the ErrorLogger.
        
        Args:
            todo_dir: Directory to store TODO files
        """
        self.todo_dir = Path(todo_dir)
        self.todo_dir.mkdir(exist_ok=True, parents=True)
    
    def log_error(
        self,
        command: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        trace: Optional[str] = None
    ) -> str:
        """
        Log an error to a TODO file.
        
        Args:
            command: The command that failed
            error: The exception that was raised
            context: Additional context about the error
            trace: Optional traceback string (if not provided, will be generated)
            
        Returns:
            Path to the created TODO file
        """
        try:
            # Generate a unique filename based on timestamp and command
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_command = "".join(c if c.isalnum() else "_" for c in command[:50])
            filename = f"{timestamp}_{safe_command}.md"
            filepath = self.todo_dir / filename
            
            # Prepare error data
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "context": context or {},
                "traceback": trace or traceback.format_exc(),
            }
            
            # Write to markdown file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# TODO: Command Error - {timestamp}\n\n")
                f.write(f"## Command\n```\n{command}\n```\n\n")
                f.write(f"## Error\n```\n{error.__class__.__name__}: {error}\n```\n\n")
                
                if context:
                    f.write("## Context\n```json\n")
                    json.dump(context, f, indent=2, ensure_ascii=False)
                    f.write("\n```\n\n")
                
                f.write("## Traceback\n```python\n")
                f.write(traceback.format_exc())
                f.write("\n```\n\n")
                
                f.write("## Suggested Fix\n")
                f.write("<!-- Add your suggested fix here -->\n\n")
                
                f.write("## Implementation Notes\n")
                f.write("<!-- Add any implementation notes here -->\n")
            
            logger.info(f"Logged error to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}", exc_info=True)
            raise
    
    @classmethod
    def get_instance(cls: Type[T]) -> T:
        """Get or create a singleton instance of ErrorLogger."""
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


def log_command_error(
    command: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    trace: Optional[str] = None
) -> str:
    """
    Log a command error to a TODO file.
    
    This is a convenience function that uses the singleton instance of ErrorLogger.
    
    Args:
        command: The command that failed
        error: The exception that was raised
        context: Additional context about the error
        trace: Optional traceback string (if not provided, will be generated)
        
    Returns:
        Path to the created TODO file
    """
    return ErrorLogger.get_instance().log_error(command, error, context, trace)


def error_handler(func: Callable) -> Callable:
    """
    Decorator to automatically log errors to TODO files.
    
    Example:
        @error_handler
        def some_command(*args, **kwargs):
            # Command implementation
            pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get command name from function
            command_name = f"{func.__module__}.{func.__name__}"
            
            # Get context from function arguments
            context = {
                "args": str(args[1:]),  # Skip 'self' for instance methods
                "kwargs": str(kwargs)
            }
            
            # Log the error
            log_command_error(command_name, e, context)
            raise
    
    return wrapper
