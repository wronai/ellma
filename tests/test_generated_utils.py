"""Tests for the generated_utils module."""
import time
import unittest
from unittest.mock import patch, MagicMock
from ellma.modules.generated_utils import (
    enhanced_error_handler, 
    PerformanceCache, 
    parallel_map,
    default_cache
)

class TestEnhancedErrorHandler(unittest.TestCase):
    """Test the enhanced_error_handler decorator."""
    
    def test_successful_execution(self):
        """Test that a function works normally without errors."""
        @enhanced_error_handler(max_retries=2)
        def test_func():
            return "success"
            
        result = test_func()
        self.assertEqual(result, "success")
    
    def test_retry_until_success(self):
        """Test that a function is retried until it succeeds."""
        mock_func = MagicMock(side_effect=[Exception("Error"), "success"])
        
        @enhanced_error_handler(max_retries=3, initial_delay=0.1)
        def test_func():
            return mock_func()
            
        result = test_func()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
    
    def test_max_retries_exceeded(self):
        """Test that the decorator gives up after max retries."""
        @enhanced_error_handler(max_retries=2, initial_delay=0.1)
        def test_func():
            raise ValueError("Persistent error")
            
        with self.assertRaises(ValueError):
            test_func()


class TestPerformanceCache(unittest.TestCase):
    """Test the PerformanceCache class."""
    
    def setUp(self):
        """Set up test case."""
        self.cache = PerformanceCache(ttl_seconds=1)
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
    
    @patch('time.time')
    def test_expiration(self, mock_time):
        """Test that cache entries expire."""
        # Set initial time
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Add an entry
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Move time forward past TTL
        mock_time.return_value = current_time + 2  # 2 seconds > 1 second TTL
        
        # Entry should be expired
        self.assertIsNone(self.cache.get("key1"))
    
    def test_clear(self):
        """Test clearing the cache."""
        self.cache.set("key1", "value1")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(len(self.cache.cache), 0)
        self.assertEqual(len(self.cache.timestamps), 0)


# Module-level functions for parallel processing tests
def square(x):
    return x * x

def fails_on_even(x):
    if x % 2 == 0:
        raise ValueError(f"Failed on {x}")
    return x * x

def slow_func(x):
    time.sleep(1)
    return x * x

class TestParallelMap(unittest.TestCase):
    """Test the parallel_map function."""
    
    def test_basic_parallel_map(self):
        """Test basic parallel execution."""
        results = parallel_map(square, [1, 2, 3, 4, 5])
        self.assertEqual(sorted(results), [1, 4, 9, 16, 25])
    
    def test_parallel_map_with_errors(self):
        """Test error handling in parallel execution."""
        with self.assertRaises(ValueError):
            parallel_map(fails_on_even, [1, 2, 3, 4, 5])
    
    def test_parallel_map_with_timeout(self):
        """Test timeout handling in parallel execution."""
        with self.assertRaises(TimeoutError):
            parallel_map(slow_func, [1, 2, 3], timeout=0.1)


class TestDefaultCache(unittest.TestCase):
    """Test the default cache instance."""
    
    def test_default_cache(self):
        """Test the default cache instance."""
        default_cache.set("test_key", "test_value")
        self.assertEqual(default_cache.get("test_key"), "test_value")
        default_cache.clear()
        self.assertIsNone(default_cache.get("test_key"))


if __name__ == "__main__":
    unittest.main()
