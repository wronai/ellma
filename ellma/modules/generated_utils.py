"""
Generated Utilities Module

This module contains automatically generated utility functions and classes
that enhance the core functionality of ELLMa. These include:
- Enhanced error handling with retry logic
- Performance caching utilities
- Parallel processing helpers
"""
import time
from functools import wraps
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, TypeVar, Generic

T = TypeVar('T')
R = TypeVar('R')

# Re-export the enhanced error handler
def enhanced_error_handler(max_retries: int = 3, initial_delay: float = 1.0):
    """
    Decorator that adds retry logic to a function.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds (will be doubled after each attempt)
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            
            # If we get here, all retries failed
            raise last_exception if last_exception else Exception("Unknown error in retry handler")
        return wrapper
    return decorator

class PerformanceCache:
    """
    A simple in-memory cache with TTL (time-to-live) support.
    """
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time in seconds before cache entries expire
        """
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            # Clean up expired entry
            del self.cache[key]
            del self.timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()

def parallel_map(
    func: Callable[[T], R],
    items: List[T],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None
) -> List[R]:
    """
    Execute a function in parallel on a list of items.
    
    Args:
        func: Function to execute
        items: List of items to process
        max_workers: Maximum number of worker processes
        timeout: Maximum time to wait for all tasks to complete
        
    Returns:
        List of results in the same order as input items
        
    Raises:
        TimeoutError: If the operation times out
        Exception: If any task raises an exception
    """
    results: List[Optional[R]] = [None] * len(items)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Start all tasks
        future_to_index = {
            executor.submit(func, item): i
            for i, item in enumerate(items)
        }
        
        # Process results as they complete
        for future in as_completed(future_to_index, timeout=timeout):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as e:
                # Store the exception to be re-raised after all tasks complete
                results[index] = e
    
    # Check for any exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            raise result
    
    return results  # type: ignore

# Global cache instance
default_cache = PerformanceCache()
