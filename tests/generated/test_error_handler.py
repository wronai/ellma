import unittest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the generated modules directory to path
sys.path.append(str(Path.home() / '.ellma' / 'evolution' / 'generated'))

class TestErrorHandler(unittest.TestCase):
    def test_enhanced_error_handler_retry(self):
        """Test that the error handler retries on failure"""
        # Import the module to test
        import generated_33 as error_handler
        
        # Create a mock function that fails twice then succeeds
        mock_func = MagicMock()
        mock_func.side_effect = [Exception('Error 1'), Exception('Error 2'), 'Success']
        
        # Apply the decorator
        wrapped_func = error_handler.enhanced_error_handler(mock_func)
        
        # Call the function
        result = wrapped_func('test_arg', kwarg='test')
        
        # Verify it was called 3 times (2 failures + 1 success)
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(result, 'Success')
    
    def test_enhanced_error_handler_gives_up_after_retries(self):
        """Test that the error handler gives up after max retries"""
        import generated_33 as error_handler
        
        # Create a mock function that always fails
        mock_func = MagicMock()
        mock_func.side_effect = Exception('Persistent error')
        
        # Apply the decorator
        wrapped_func = error_handler.enhanced_error_handler(mock_func)
        
        # Verify it raises an exception after max retries
        with self.assertRaises(Exception):
            wrapped_func()
        self.assertEqual(mock_func.call_count, 3)

if __name__ == '__main__':
    unittest.main()
