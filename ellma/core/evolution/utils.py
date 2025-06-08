"""
Evolution Utilities

This module provides utility functions for the evolution process.
"""

import os
import sys
import time
import random
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

import numpy as np
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

logger = logging.getLogger(__name__)

def setup_evolution_environment(working_dir: Path) -> bool:
    """Set up the environment for evolution.
    
    Args:
        working_dir: Directory to use for evolution artifacts
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        # Create necessary directories
        working_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (working_dir / 'checkpoints').mkdir(exist_ok=True)
        (working_dir / 'logs').mkdir(exist_ok=True)
        (working_dir / 'modules').mkdir(exist_ok=True)
        
        # Initialize a git repository for version control
        if not (working_dir / '.git').exists():
            try:
                subprocess.run(['git', 'init'], cwd=working_dir, check=True, capture_output=True)
                with open(working_dir / '.gitignore', 'w') as f:
                    f.write('__pycache__\n*.pyc\n*.pyo\n*.pyd\n*.so\n')
            except (subprocess.SubprocessError, OSError) as e:
                logger.warning(f"Could not initialize git repository: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup evolution environment: {e}")
        return False


def check_system_resources(config: Any) -> bool:
    """Check if system has sufficient resources for evolution.
    
    Args:
        config: Configuration object with resource limits
        
    Returns:
        True if resources are sufficient, False otherwise
    """
    try:
        import psutil
        
        # Check memory
        mem = psutil.virtual_memory()
        if mem.available < config.max_memory_mb * 1024 * 1024:  # Convert MB to bytes
            logger.warning(f"Insufficient memory: {mem.available/1024/1024:.1f}MB available, "
                         f"{config.max_memory_mb}MB required")
            return False
            
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > config.max_cpu_percent:
            logger.warning(f"High CPU usage: {cpu_percent}% > {config.max_cpu_percent}%")
            return False
            
        # Check disk space
        disk = psutil.disk_usage(str(Path.cwd()))
        min_disk_space = 100 * 1024 * 1024  # 100MB minimum
        if disk.free < min_disk_space:
            logger.warning(f"Insufficient disk space: {disk.free/1024/1024:.1f}MB available, "
                         f"{min_disk_space/1024/1024:.0f}MB required")
            return False
            
        return True
        
    except ImportError:
        logger.warning("psutil not available, skipping resource checks")
        return True  # Assume resources are sufficient if we can't check
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return False


def cleanup_resources() -> None:
    """Clean up temporary files and resources."""
    # Clean up any temporary files
    temp_dir = Path(tempfile.gettempdir())
    for temp_file in temp_dir.glob('ellma_evolution_*'):
        try:
            if temp_file.is_file():
                temp_file.unlink()
            elif temp_file.is_dir():
                shutil.rmtree(temp_file)
        except Exception as e:
            logger.warning(f"Failed to clean up {temp_file}: {e}")
    
    # Clear any cached modules that might have been dynamically imported
    for module in list(sys.modules.keys()):
        if module.startswith('ellma.evolution.generated'):
            del sys.modules[module]


def log_evolution_result(result: Dict[str, Any]) -> None:
    """Log the results of an evolution run.
    
    Args:
        result: Dictionary containing evolution results
    """
    if not result:
        return
        
    logger.info("=" * 80)
    logger.info("EVOLUTION RESULTS")
    logger.info("=" * 80)
    
    for key, value in result.items():
        logger.info(f"{key}: {value}")
    
    logger.info("=" * 80)


def time_execution(func: Callable) -> Callable:
    """Decorator to measure and log execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper


def with_retry(max_retries: int = 3, delay: float = 1.0, 
              exceptions: tuple = (Exception,)) -> Callable:
    """Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded: {e}")
                        raise
                    logger.warning(f"Attempt {retries}/{max_retries} failed: {e}")
                    time.sleep(delay * (2 ** (retries - 1)))  # Exponential backoff
        return wrapper
    return decorator


def get_progress_bar(description: str = "Processing") -> Progress:
    """Create a rich progress bar.
    
    Args:
        description: Description to display next to the progress bar
        
    Returns:
        A configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[progress.description]{description}"),
        BarColumn(bar_width=None),
        transient=True,
    )


def validate_module_code(code: str) -> Tuple[bool, str]:
    """Validate that code is syntactically correct Python.
    
    Args:
        code: Python code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}, offset {e.offset}"
    except Exception as e:
        return False, f"Error: {str(e)}"
