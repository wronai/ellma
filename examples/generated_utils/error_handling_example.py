"""
Enhanced Error Handling Example

This example demonstrates how to use the enhanced_error_handler decorator
to automatically retry failed operations with exponential backoff.
"""
import random
import time
from ellma.modules import enhanced_error_handler

def simulate_unreliable_operation():
    """Simulate an operation that might fail randomly."""
    if random.random() < 0.7:  # 70% chance of failure
        raise ConnectionError("Failed to connect to the service")
    return "Operation successful"

@enhanced_error_handler(max_retries=5, initial_delay=1.0, backoff_factor=2.0)
def reliable_operation():
    """A function that will automatically retry on failure."""
    print("Attempting operation...")
    result = simulate_unreliable_operation()
    print("Operation succeeded!")
    return result

def main():
    print("=== Enhanced Error Handling Example ===\n")
    
    print("This example simulates an unreliable operation that has a 70% chance of failing.")
    print("The @enhanced_error_handler decorator will automatically retry failed operations.\n")
    
    try:
        start_time = time.time()
        result = reliable_operation()
        elapsed = time.time() - start_time
        print(f"\n✅ Final result: {result}")
        print(f"⌛ Total time: {elapsed:.2f} seconds")
    except Exception as e:
        print(f"\n❌ All retries failed: {e}")

if __name__ == "__main__":
    main()
