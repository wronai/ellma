"""
Error logging utilities for the ELLMa system.

This module provides functions for consistent error handling and logging
across the application.
"""
import logging
import traceback
from typing import Any, Optional, Type, TypeVar, Callable
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

def log_error(error: Exception, context: str = "", level: str = "error") -> None:
    """
    Log an error with context and stack trace.
    
    Args:
        error: The exception that was raised
        context: Additional context about where the error occurred
        level: Logging level ('error', 'warning', 'info', 'debug')
    """
    log_method = getattr(logger, level.lower(), logger.error)
    
    error_msg = f"{context}: {str(error)}\n"
    error_msg += f"Type: {error.__class__.__name__}\n"
    error_msg += "Traceback (most recent call last):\n"
    error_msg += "\n".join(traceback.format_tb(error.__traceback__))
    
    log_method(error_msg)

def error_handler(
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    default: Any = None,
    context: str = "",
    reraise: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator to handle exceptions in functions and methods.
    
    Args:
        exceptions: Tuple of exception types to catch
        default: Default value to return if an exception occurs
        context: Context string for error messages
        reraise: Whether to re-raise the exception after logging
        
    Returns:
        Decorated function that handles exceptions
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                log_error(e, context=context or f"Error in {func.__name__}")
                if reraise:
                    raise
                return default
        return wrapper
    return decorator
