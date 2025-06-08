"""
Combined Utilities Example

This example demonstrates how to combine all three generated utilities
(enhanced error handling, performance caching, and parallel processing)
to build a robust and efficient data processing pipeline.
"""
import time
import random
from typing import List, Dict, Any, Optional
from ellma.modules import (
    enhanced_error_handler,
    PerformanceCache,
    parallel_map,
    default_cache
)

# Global cache for API responses
api_cache = PerformanceCache(ttl_seconds=300)  # 5 minute TTL

@enhanced_error_handler(max_retries=3, initial_delay=1.0)
def fetch_user_data(user_id: str) -> Dict[str, Any]:
    """
    Fetch user data from an API with retry logic and caching.
    
    Args:
        user_id: The ID of the user to fetch data for
        
    Returns:
        Dictionary containing user data
    """
    # Check cache first
    cache_key = f"user:{user_id}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        print(f"  [Cache hit] User {user_id}")
        return cached
    
    print(f"  [API call] Fetching user {user_id}...")
    
    # Simulate API call with random failures
    if random.random() < 0.3:  # 30% chance of failure
        raise ConnectionError(f"Failed to fetch user {user_id}")
    
    # Simulate API latency
    time.sleep(0.5)
    
    # Generate mock user data
    user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "joined_at": int(time.time()) - random.randint(0, 1000000),
        "last_active": int(time.time()),
        "preferences": {
            "theme": random.choice(["light", "dark"]),
            "notifications": random.choice([True, False])
        }
    }
    
    # Cache the result
    api_cache.set(cache_key, user_data)
    return user_data

def process_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user data (e.g., calculate statistics, transform data).
    
    Args:
        user_data: Raw user data from the API
        
    Returns:
        Processed user data
    """
    # Simulate processing time
    time.sleep(0.1)
    
    # Calculate some statistics
    days_since_joined = (time.time() - user_data["joined_at"]) / (24 * 3600)
    
    # Return enriched data
    return {
        "user_id": user_data["id"],
        "username": user_data["name"],
        "email": user_data["email"],
        "days_since_joined": int(days_since_joined),
        "theme_preference": user_data["preferences"]["theme"],
        "notifications_enabled": user_data["preferences"]["notifications"],
        "processed_at": int(time.time())
    }

def main():
    print("=== Combined Utilities Example ===\n")
    
    # Generate some user IDs
    user_ids = [str(i) for i in range(1, 11)]
    
    # Track metrics
    start_time = time.time()
    
    print("Processing users...")
    
    # Fetch and process user data in parallel
    try:
        # Step 1: Fetch all user data in parallel with error handling and caching
        users_data = parallel_map(
            fetch_user_data,
            user_ids,
            max_workers=4,
            timeout=30.0  # 30 second timeout for all operations
        )
        
        # Step 2: Process the data in parallel
        processed_users = parallel_map(
            process_user_data,
            users_data,
            max_workers=4
        )
        
        # Calculate statistics
        total_users = len(processed_users)
        themes = [user["theme_preference"] for user in processed_users]
        light_theme_users = themes.count("light")
        dark_theme_users = themes.count("dark")
        notifications_on = sum(1 for user in processed_users if user["notifications_enabled"])
        
        # Print summary
        elapsed = time.time() - start_time
        print("\n=== Results ===")
        print(f"Processed {total_users} users in {elapsed:.2f} seconds")
        print(f"- Light theme: {light_theme_users} users")
        print(f"- Dark theme: {dark_theme_users} users")
        print(f"- Notifications enabled: {notifications_on} users")
        
        # Show a sample of the processed data
        print("\nSample user:")
        import pprint
        pprint.pprint(processed_users[0])
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    
    # Show cache statistics
    print(f"\nCache stats: {len(api_cache._cache)} items in cache")

if __name__ == "__main__":
    main()
