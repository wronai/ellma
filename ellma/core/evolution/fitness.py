"""
Fitness Evaluation

This module handles the evaluation of candidate solutions during evolution.
"""

import ast
import inspect
import time
from typing import Dict, Any, Callable, List, Tuple
from pathlib import Path
import importlib.util
import sys
import os

from ellma.core.evolution.exceptions import TestFailure


def evaluate_module(module_path: Path, test_cases: List[Callable]) -> Dict[str, Any]:
    """Evaluate a module using the provided test cases.
    
    Args:
        module_path: Path to the module to evaluate
        test_cases: List of test case functions
        
    Returns:
        Dictionary containing evaluation results
        
    Raises:
        TestFailure: If any test case fails
    """
    results = {
        'passed': 0,
        'failed': 0,
        'errors': [],
        'coverage': 0.0,
        'performance': 0.0,
        'start_time': time.time()
    }
    
    try:
        # Load the module
        module_name = module_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_path}")
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Run test cases
        for test_case in test_cases:
            test_name = test_case.__name__
            try:
                test_case(module)
                results['passed'] += 1
            except AssertionError as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': test_name,
                    'type': 'AssertionError',
                    'message': str(e)
                })
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': test_name,
                    'type': type(e).__name__,
                    'message': str(e)
                })
        
        # Calculate coverage (simplified)
        results['coverage'] = calculate_coverage(module_path)
        
        # Calculate performance score
        results['performance'] = 1.0 / (time.time() - results['start_time'] + 1e-6)
        
        # Calculate overall fitness
        results['fitness'] = (
            0.4 * (results['passed'] / len(test_cases)) +  # Test pass rate
            0.3 * results['coverage'] +                    # Code coverage
            0.2 * min(1.0, results['performance'] / 1000) +  # Performance
            0.1 * (1.0 - len(inspect.getmembers(module, inspect.isfunction)) / 100)  # Complexity
        )
        
        if results['failed'] > 0:
            raise TestFailure(f"{results['failed']} test(s) failed")
            
        return results
        
    except Exception as e:
        results['errors'].append({
            'test': 'module_import',
            'type': type(e).__name__,
            'message': str(e)
        })
        results['fitness'] = 0.0
        return results


def calculate_coverage(module_path: Path) -> float:
    """Calculate code coverage for a module.
    
    This is a simplified implementation. In a real system, you would
    use a proper coverage tool like coverage.py.
    """
    try:
        with open(module_path, 'r') as f:
            source = f.read()
        
        # Simple heuristic: ratio of non-empty, non-comment lines to total lines
        lines = source.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return 0.0
            
        code_lines = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                code_lines += 1
                
        return code_lines / total_lines
        
    except Exception:
        return 0.0


def validate_module(module_path: Path) -> bool:
    """Validate that a module can be imported and has valid syntax."""
    try:
        # Check syntax
        with open(module_path, 'r') as f:
            ast.parse(f.read())
        
        # Try importing
        module_name = module_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            return False
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return True
        
    except (SyntaxError, ImportError, Exception):
        return False
