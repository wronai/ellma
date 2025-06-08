"""
Performance Cache Example

This example demonstrates how to use the PerformanceCache class
for efficient data caching with time-based expiration.
"""
import time
from ellma.modules import PerformanceCache

def expensive_operation(key):
    """Simulate an expensive operation (e.g., API call, database query)."""
    print(f"  Performing expensive operation for {key}...")
    time.sleep(1)  # Simulate processing time
    return f"result_for_{key}_{int(time.time())}"

def main():
    print("=== Performance Cache Example ===\n")
    
    # Create a cache with 5-second TTL
    cache = PerformanceCache(ttl_seconds=5)
    
    # First call - will compute and cache the result
    print("First call (not in cache):")
    result1 = cache.get("key1", lambda: expensive_operation("key1"))
    print(f"  Result: {result1}")
    
    # Second call - will use cached result
    print("\nSecond call (should use cache):")
    result2 = cache.get("key1", lambda: expensive_operation("key1"))
    print(f"  Result: {result2}")
    
    # Wait for cache to expire
    print("\nWaiting for cache to expire (5 seconds)...")
    time.sleep(6)
    
    # Third call - cache expired, will compute again
    print("\nThird call (after expiration):")
    result3 = cache.get("key1", lambda: expensive_operation("key1"))
    print(f"  Result: {result3}")
    
    # Using the default global cache
    print("\nUsing the default global cache:")
    from ellma.modules import default_cache
    
    # This will be cached globally
    default_cache.set("app:config", {"theme": "dark", "version": "1.0.0"})
    config = default_cache.get("app:config")
    print(f"  Cached config: {config}")

if __name__ == "__main__":
    main()
