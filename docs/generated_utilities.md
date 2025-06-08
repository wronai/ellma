# 🛠 Generated Utilities

ELLMa includes a set of powerful, self-generated utilities that help with common programming tasks. These utilities are automatically tested and maintained by the system.

## Table of Contents
- [Enhanced Error Handler](#enhanced-error-handler)
- [Performance Cache](#performance-cache)
- [Parallel Processing](#parallel-processing)
- [Combining Utilities](#combining-utilities)
- [API Reference](#api-reference)

## Enhanced Error Handler

Automatically retry failed operations with exponential backoff.

### Features
- Configurable number of retries
- Exponential backoff between retries
- Customizable exception handling
- Detailed logging of retry attempts

### Example

```python
from ellma.modules import enhanced_error_handler
import requests

@enhanced_error_handler(max_retries=3, initial_delay=1.0)
def fetch_data(url):
    """Fetch data from an API with automatic retries."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Will automatically retry on failure
data = fetch_data("https://api.example.com/data")
```

## Performance Cache

In-memory cache with time-based expiration.

### Features
- Time-to-live (TTL) for cached items
- Thread-safe operations
- Global default cache instance
- Simple key-value interface

### Example

```python
from ellma.modules import PerformanceCache, default_cache

# Create a custom cache
cache = PerformanceCache(ttl_seconds=300)  # 5 minute TTL

# Store and retrieve data
cache.set("user:1", {"name": "Alice", "role": "admin"})
user = cache.get("user:1")

# Use the default global cache
default_cache.set("app:config", {"theme": "dark", "notifications": True})
```

## Parallel Processing

Easily parallelize CPU-bound or I/O-bound tasks.

### Features
- Simple interface similar to `map()`
- Configurable number of worker processes
- Timeout support
- Automatic error propagation

### Example

```python
from ellma.modules import parallel_map

def process_item(item):
    # CPU-intensive or I/O-bound work
    return item ** 2

# Process items in parallel
results = parallel_map(process_item, range(10), max_workers=4)
```

## Combining Utilities

These utilities work well together. Here's a more complex example:

```python
from ellma.modules import enhanced_error_handler, PerformanceCache, parallel_map
import requests

# Create a cache with 1-hour TTL
cache = PerformanceCache(ttl_seconds=3600)


@enhanced_error_handler(max_retries=3)
def fetch_user_data(user_id):
    """Fetch user data with caching and retries."""
    # Check cache first
    cached = cache.get(f"user:{user_id}")
    if cached is not None:
        return cached
    
    # Fetch from API if not in cache
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    data = response.json()
    
    # Cache the result
    cache.set(f"user:{user_id}", data)
    return data

def process_users(user_ids):
    """Process multiple users in parallel."""
    return parallel_map(fetch_user_data, user_ids, max_workers=4)

# Process multiple users efficiently
users = process_users([1, 2, 3, 4, 5])
```

## API Reference

### `enhanced_error_handler`

```python
def enhanced_error_handler(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Create a decorator that adds retry logic to a function.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch and retry on
    """
```

### `PerformanceCache`

```python
class PerformanceCache:
    """Thread-safe cache with TTL support."""
    
    def __init__(self, ttl_seconds: float = 300.0):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
    
    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache."""
    
    def clear(self) -> None:
        """Clear all items from the cache."""

# Global cache instance
default_cache = PerformanceCache()
```

### `parallel_map`

```python
def parallel_map(
    func: Callable[[T], R],
    iterable: Iterable[T],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None
) -> List[R]:
    """
    Apply function to each item in iterable in parallel.
    
    Args:
        func: Function to apply
        iterable: Items to process
        max_workers: Maximum number of worker processes
        timeout: Maximum time to wait for all tasks to complete
    """
```
