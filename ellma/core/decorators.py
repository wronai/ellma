"""
Decorators for adding security and dependency checking to functions.
"""

import functools
import inspect
import logging
from typing import Callable, List, Optional, Any, Dict, Type, TypeVar, Union

from ellma.core.security import Dependency, ensure_dependencies, SecurityError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Callable[..., Any])

def secure(dependencies: Optional[List[Dependency]] = None, 
          enforce_security: bool = True) -> Callable[[T], T]:
    """
    Decorator to ensure function dependencies are met before execution.
    
    Args:
        dependencies: List of dependencies required by the function
        enforce_security: If True, raises SecurityError if dependencies aren't met
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if dependencies:
                if not ensure_dependencies(dependencies):
                    error_msg = f"Failed to resolve dependencies for {func.__name__}"
                    if enforce_security:
                        raise SecurityError(error_msg)
                    logger.warning(f"{error_msg} - continuing anyway")
            
            # Get the function signature for better error messages
            sig = inspect.signature(func)
            try:
                # Bind the arguments to check them
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Call the original function
                return func(*bound_args.args, **bound_args.kwargs)
                
            except TypeError as e:
                # Provide better error messages for argument mismatches
                raise TypeError(f"{e} in {func.__name__}{sig}") from e
                
        return wrapper  # type: ignore
    return decorator

def validate_input(validator: Callable[[Any], bool], 
                  error_message: str = "Invalid input") -> Callable[[T], T]:
    """
    Decorator to validate function inputs.
    
    Args:
        validator: Function that takes input and returns True if valid
        error_message: Message to raise if validation fails
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate all arguments
            for arg in args:
                if not validator(arg):
                    raise ValueError(f"{error_message}: {arg}")
            for _, value in kwargs.items():
                if not validator(value):
                    raise ValueError(f"{error_message}: {value}")
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator

def log_execution(log_result: bool = False, 
                 log_args: bool = True,
                 log_kwargs: bool = True) -> Callable[[T], T]:
    """
    Decorator to log function execution details.
    
    Args:
        log_result: Whether to log the function's return value
        log_args: Whether to log positional arguments
        log_kwargs: Whether to log keyword arguments
        
    Returns:
        Decorated function
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log function call
            call_str = f"{func.__name__} called"
            if log_args and args:
                call_str += f" with args: {args}"
            if log_kwargs and kwargs:
                call_str += f" with kwargs: {kwargs}"
            logger.debug(call_str)
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log the result if requested
            if log_result:
                logger.debug(f"{func.__name__} returned: {result}")
                
            return result
            
        return wrapper  # type: ignore
    return decorator

class SecureContext:
    """
    Context manager for secure code execution with dependency management.
    """
    
    def __init__(self, dependencies: Optional[List[Dependency]] = None, 
                 enforce_security: bool = True):
        self.dependencies = dependencies or []
        self.enforce_security = enforce_security
        
    def __enter__(self):
        if self.dependencies and not ensure_dependencies(self.dependencies):
            error_msg = "Failed to resolve required dependencies"
            if self.enforce_security:
                raise SecurityError(error_msg)
            logger.warning(f"{error_msg} - continuing anyway")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        if exc_type is not None:
            logger.error(f"Error in secure context: {exc_val}", exc_info=True)
        return False  # Don't suppress exceptions

# Example usage
if __name__ == "__main__":
    # Example dependency
    numpy_dep = Dependency(
        name="numpy",
        package_name="numpy",
        min_version="1.20.0"
    )
    
    @secure(dependencies=[numpy_dep])
    def process_data(data):
        import numpy as np
        return np.array(data).mean()
    
    # This will raise SecurityError if numpy is not installed or version is too old
    try:
        result = process_data([1, 2, 3, 4, 5])
        print(f"Result: {result}")
    except SecurityError as e:
        print(f"Security error: {e}")
