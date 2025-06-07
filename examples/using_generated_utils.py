"""
Example: Using Generated Utilities

This example demonstrates how to use the generated utilities in the ELLMa framework.
It shows practical examples of the enhanced error handler, performance cache, and parallel processing utilities.
"""
import time
from ellma.modules import (
    enhanced_error_handler,
    PerformanceCache,
    parallel_map,
    default_cache
)

def example_error_handler():
    """Example of using the enhanced error handler."""
    print("\n=== Enhanced Error Handler Example ===")
    
    @enhanced_error_handler(max_retries=3, initial_delay=0.5)
    def fetch_data(url):
        """Simulate a flaky API call."""
        if "example" in url:
            print(f"  Successfully fetched data from {url}")
            return f"Data from {url}"
        raise ConnectionError(f"Could not connect to {url}")
    
    # This will succeed after retries
    print("Attempting to fetch data (will retry on failure):")
    result = fetch_data("https://api.example.com/data")
    print(f"  Final result: {result}")
    
    # This will fail after max retries
    try:
        print("\nAttempting to fetch from invalid URL (will fail after retries):")
        fetch_data("https://invalid-url")
    except Exception as e:
        print(f"  Expected error: {e}")

def example_performance_cache():
    """Example of using the performance cache."""
    print("\n=== Performance Cache Example ===")
    
    # Create a cache with 2-second TTL
    cache = PerformanceCache(ttl_seconds=2)
    
    # Store and retrieve values
    print("Caching values...")
    cache.set("user:1", {"id": 1, "name": "Alice"})
    cache.set("user:2", {"id": 2, "name": "Bob"})
    
    # Retrieve values
    print(f"User 1: {cache.get('user:1')}")
    print(f"User 2: {cache.get('user:2')}")
    print(f"Non-existent user: {cache.get('user:3')}")
    
    # Wait for cache to expire
    print("\nWaiting for cache to expire...")
    time.sleep(2.1)
    
    # Values should be expired now
    print(f"After expiration - User 1: {cache.get('user:1')}")
    print(f"Using default_cache - User 2: {default_cache.get('user:2')}")
    
    # Using the default cache
    default_cache.set("app:config", {"theme": "dark", "notifications": True})
    print(f"Default cache - App config: {default_cache.get('app:config')}")

# Module-level function for parallel processing
def process_item(item):
    """A CPU-bound function for processing items."""
    # Simulate some processing
    time.sleep(0.2)
    return f"Processed {item}"

def example_parallel_processing():
    """Example of parallel processing."""
    print("\n=== Parallel Processing Example ===")
    
    items = [f"item_{i}" for i in range(5)]
    
    print("Processing items sequentially...")
    start_time = time.time()
    results = [process_item(item) for item in items]
    seq_time = time.time() - start_time
    print(f"  Took {seq_time:.2f} seconds")
    
    print("\nProcessing items in parallel...")
    start_time = time.time()
    results = parallel_map(process_item, items, max_workers=3)
    parallel_time = time.time() - start_time
    print(f"  Took {parallel_time:.2f} seconds")
    print(f"  Results: {results}")
    
    print(f"\nSpeedup: {seq_time/parallel_time:.1f}x")

if __name__ == "__main__":
    example_error_handler()
    example_performance_cache()
    example_parallel_processing()
