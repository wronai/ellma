import unittest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the generated modules directory to path
sys.path.append(str(Path.home() / '.ellma' / 'evolution' / 'generated'))

class TestPerformanceCache(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        import generated_34 as cache_module
        self.cache = cache_module.PerformanceCache()
    
    def test_cache_set_get(self):
        """Test basic cache set and get operations"""
        # Set a value
        self.cache.set('test_key', 'test_value')
        
        # Get the value
        result = self.cache.get('test_key')
        
        # Verify the value
        self.assertEqual(result, 'test_value')
    
    @patch('time.time')
    def test_cache_expiration(self, mock_time):
        """Test that cache entries expire after TTL"""
        # Set up initial time
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Set a value
        self.cache.set('test_key', 'test_value')
        
        # Verify value is still there
        self.assertEqual(self.cache.get('test_key'), 'test_value')
        
        # Fast forward time past TTL (5 minutes + 1 second = 301 seconds)
        mock_time.return_value = current_time + 301
        
        # Verify value has expired
        self.assertIsNone(self.cache.get('test_key'))
    
    def test_cache_nonexistent_key(self):
        """Test getting a non-existent key returns None"""
        result = self.cache.get('nonexistent_key')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
