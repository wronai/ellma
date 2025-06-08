"""
Security and dependency management layer for ELLMa.

This module provides a security wrapper and dependency management system
that ensures all required dependencies are available and properly configured.
"""

import sys
import importlib
import subprocess
import pkg_resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Dependency:
    """Represents a Python package dependency."""
    name: str
    package_name: Optional[str] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    required: bool = True
    install_command: Optional[str] = None
    
    def __post_init__(self):
        self.package_name = self.package_name or self.name

class SecurityError(Exception):
    """Base class for security-related exceptions."""
    pass

class DependencyError(SecurityError):
    """Raised when there's an issue with dependencies."""
    pass

class EnvironmentError(SecurityError):
    """Raised when there's an issue with the environment."""
    pass

def check_dependency(dep: Dependency) -> Tuple[bool, str]:
    """Check if a dependency is installed and meets version requirements."""
    try:
        module = importlib.import_module(dep.name)
        
        if dep.min_version or dep.max_version:
            version = getattr(module, '__version__', '0.0.0')
            if dep.min_version and pkg_resources.parse_version(version) < pkg_resources.parse_version(dep.min_version):
                return False, f"Version {version} is below required {dep.min_version}"
            if dep.max_version and pkg_resources.parse_version(version) > pkg_resources.parse_version(dep.max_version):
                return False, f"Version {version} is above maximum {dep.max_version}"
                
        return True, f"{dep.name} is installed and compatible"
    except ImportError:
        return False, f"{dep.name} is not installed"

def install_dependency(dep: Dependency) -> bool:
    """Install a dependency using pip or custom command."""
    try:
        if dep.install_command:
            cmd = dep.install_command
        else:
            cmd = [sys.executable, "-m", "pip", "install"]
            if dep.min_version and not dep.max_version:
                cmd.append(f"{dep.package_name}>={dep.min_version}")
            elif dep.max_version and not dep.min_version:
                cmd.append(f"{dep.package_name}<={dep.max_version}")
            elif dep.min_version and dep.max_version:
                cmd.append(f"{dep.package_name}>={dep.min_version},<={dep.max_version}")
            else:
                cmd.append(dep.package_name)
        
        if isinstance(cmd, str):
            cmd = cmd.split()
            
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Successfully installed {dep.name}: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {dep.name}: {e.stderr}")
        return False

def ensure_dependencies(dependencies: List[Dependency]) -> bool:
    """Ensure all dependencies are installed and compatible."""
    success = True
    for dep in dependencies:
        is_ok, message = check_dependency(dep)
        if not is_ok:
            logger.warning(f"Dependency issue: {message}")
            if dep.required:
                logger.info(f"Attempting to install {dep.name}...")
                if not install_dependency(dep):
                    success = False
                    if dep.required:
                        logger.error(f"Failed to install required dependency: {dep.name}")
                    else:
                        logger.warning(f"Optional dependency {dep.name} could not be installed")
    return success

def secure_import(module_name: str, dependencies: List[Dependency] = None) -> Any:
    """Safely import a module after ensuring dependencies are met."""
    if dependencies:
        if not ensure_dependencies(dependencies):
            raise DependencyError(f"Failed to resolve dependencies for {module_name}")
    
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        raise

class SecurityContext:
    """Context manager for secure code execution."""
    
    def __init__(self, dependencies: List[Dependency] = None):
        self.dependencies = dependencies or []
        self.original_path = None
    
    def __enter__(self):
        # Save original sys.path
        self.original_path = sys.path.copy()
        
        # Ensure dependencies are installed
        if not ensure_dependencies(self.dependencies):
            raise DependencyError("Failed to resolve required dependencies")
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original sys.path
        if self.original_path is not None:
            sys.path = self.original_path
        
        # Handle exceptions if needed
        if exc_type is not None:
            logger.error(f"Error in secure context: {exc_val}", exc_info=True)
            # Don't suppress the exception
            return False
        return True

def secure_execute(code: str, globals_dict: Optional[dict] = None, locals_dict: Optional[dict] = None) -> Any:
    """
    Execute code in a secure context.
    
    Args:
        code: The code to execute
        globals_dict: Global variables dictionary
        locals_dict: Local variables dictionary
        
    Returns:
        The result of the code execution
    """
    if globals_dict is None:
        globals_dict = {}
    if locals_dict is None:
        locals_dict = {}
    
    # Basic security checks
    forbidden_imports = ['os', 'sys', 'subprocess', 'importlib', 'ctypes']
    for imp in forbidden_imports:
        if f'import {imp}' in code or f'from {imp} ' in code:
            raise SecurityError(f"Forbidden import detected: {imp}")
    
    try:
        # Execute in a restricted environment
        exec_globals = {
            '__builtins__': {
                '__import__': __import__,
                'print': print,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'type': type,
                'object': object,
            }
        }
        
        # Add allowed globals
        exec_globals.update(globals_dict)
        
        # Execute the code
        exec(code, exec_globals, locals_dict)
        
        # Return any result if the code is an expression
        if code.strip() and not code.strip().startswith(('def ', 'class ', 'import ', 'from ')):
            return eval(code, exec_globals, locals_dict)
            
    except Exception as e:
        logger.error(f"Error in secure_execute: {e}", exc_info=True)
        raise SecurityError(f"Failed to execute code: {e}") from e
