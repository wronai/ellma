"""
Concurrency and rate limiting utilities.
"""

import time
import threading
from typing import Any, Callable, Optional, TypeVar, Generic, Dict, List, Tuple
from dataclasses import dataclass, field
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, Future

T = TypeVar('T')

@dataclass
class RateLimiter:
    """Simple rate limiter for controlling access to resources."""
    
    max_calls: int
    time_window: float
    calls: List[float] = field(default_factory=list)
    
    def acquire(self) -> bool:
        """
        Try to acquire permission for a call.

        Returns:
            True if call is allowed
        """
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
    
    def wait_time(self) -> float:
        """
        Get time to wait before next call is allowed.

        Returns:
            Wait time in seconds
        """
        if not self.calls or len(self.calls) < self.max_calls:
            return 0.0
            
        now = time.time()
        oldest_call = self.calls[0]
        time_since_oldest = now - oldest_call
        
        if time_since_oldest >= self.time_window:
            return 0.0
            
        return self.time_window - time_since_oldest


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if not self.last_failure_time:
            return True
        return (time.time() - self.last_failure_time) > self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
        self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class TaskPool:
    """Simple task pool for parallel execution."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize task pool.

        Args:
            max_workers: Maximum number of worker threads
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: List[Future] = []
    
    def submit(self, fn: Callable[..., T], *args, **kwargs) -> Future[T]:
        """
        Submit a task to the pool.

        Args:
            fn: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Future representing the result
        """
        future = self.executor.submit(fn, *args, **kwargs)
        self.futures.append(future)
        return future
    
    def wait_all(self, timeout: Optional[float] = None) -> List[Any]:
        """
        Wait for all tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            List of results
        """
        results = []
        for future in self.futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the task pool.

        Args:
            wait: If True, wait for all tasks to complete
        """
        self.executor.shutdown(wait=wait)
