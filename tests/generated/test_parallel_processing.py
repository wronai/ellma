import unittest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
from concurrent.futures import ProcessPoolExecutor

# Add the generated modules directory to path
sys.path.append(str(Path.home() / '.ellma' / 'evolution' / 'generated'))

# Module-level functions for multiprocessing compatibility
def square(x):
    """Test function that squares its input"""
    return x * x

def failing_function(x):
    """Test function that fails for input 3"""
    if x == 3:
        raise ValueError(f"Test error for input {x}")
    return x * x

class TestParallelProcessing(unittest.TestCase):
    def test_parallel_processing_example(self):
        """Test that parallel processing works as expected"""
        # This test verifies the pattern shown in generated_37.py
        test_data = [1, 2, 3, 4, 5]
        expected_results = [1, 4, 9, 16, 25]
        
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(square, test_data))
            
        self.assertEqual(results, expected_results)
    
    def test_parallel_processing_with_exceptions(self):
        """Test that exceptions in parallel processing are handled"""
        test_data = [1, 2, 3, 4]
        
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(failing_function, x) for x in test_data]
            
            results = []
            for future in futures:
                try:
                    results.append(future.result())
                except ValueError as e:
                    self.assertIn("Test error", str(e))
        
        # Should have processed all items, even with failures
        self.assertEqual(len(results), 3)  # 4 items - 1 failure
        # Sort because the order of results is not guaranteed
        self.assertEqual(sorted(results), [1, 4, 16])  # 2*2=4 is missing due to failure

if __name__ == '__main__':
    unittest.main()
