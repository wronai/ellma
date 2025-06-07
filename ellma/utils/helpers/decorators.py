"""
Useful decorators for common patterns.
"""

import time
import functools
from typing import Any, Callable, Optional, TypeVar, cast
from functools import wraps
from datetime import datetime, timedelta

T = TypeVar('T', bound=Callable[..., Any])

def timeout_decorator(seconds: int, default_return=None):
    """
    Decorator to add timeout to function execution

    Args:
        seconds: Timeout in seconds
        default_return: Value to return on timeout
    """
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def _handle_timeout(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set the signal handler and a timeout
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                return default_return
            finally:
                # Disable the alarm
                signal.alarm(0)
        
        return cast(T, wrapper)
    return decorator

def retry_decorator(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function execution on failure

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier for delay
    """
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break
                        
                    time.sleep(delay)
                    delay *= backoff
            
            raise last_exception or Exception("Retry failed")
        
        return cast(T, wrapper)
    return decorator

def memoize_decorator(ttl_seconds: Optional[int] = None):
    """
    Decorator to memoize function results with optional TTL

    Args:
        ttl_seconds: Time to live for cached results in seconds
    """
    def decorator(func: T) -> T:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a key based on function arguments
            key = (args, frozenset(kwargs.items()))
            
            # Check if result is in cache and still valid
            if key in cache:
                result, timestamp = cache[key]
                if ttl_seconds is None or (time.time() - timestamp) < ttl_seconds:
                    return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        
        return cast(T, wrapper)
    return decorator

def debounce(wait_seconds: float):
    """
    Debounce decorator - only execute function after specified delay
    without new calls

    Args:
        wait_seconds: Delay in seconds
    """
    def decorator(func: T) -> T:
        last_called = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            
            now = time.time()
            if now - last_called >= wait_seconds:
                last_called = now
                return func(*args, **kwargs)
        
        return cast(T, wrapper)
    return decorator

def throttle(rate_limit: float):
    """
    Throttle decorator - limit function execution rate

    Args:
        rate_limit: Minimum seconds between calls
    """
    def decorator(func: T) -> T:
        last_called = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            
            now = time.time()
            time_since_last_call = now - last_called
            
            if time_since_last_call < rate_limit:
                time.sleep(rate_limit - time_since_last_call)
            
            last_called = time.time()
            return func(*args, **kwargs)
        
        return cast(T, wrapper)
    return decorator
