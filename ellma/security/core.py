"""
Core security and environment management for ELLMa.
"""

import os
import sys
import subprocess
import shutil
import venv
import importlib
import importlib.metadata
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EnvironmentStatus(Enum):
    VALID = "valid"
    MISSING_DEPS = "missing_dependencies"
    INVALID_PYTHON = "invalid_python_version"
    NOT_IN_VENV = "not_in_venv"
    MISSING_POETRY = "missing_poetry"
    POETRY_ERROR = "poetry_error"

@dataclass
class EnvironmentCheck:
    status: EnvironmentStatus
    missing_deps: List[str] = None
    current_python: str = None
    required_python: str = None
    error: str = None

class EnvironmentError(Exception):
    """Base class for environment-related errors."""
    pass

class DependencyError(EnvironmentError):
    """Error related to dependency management."""
    pass

class SecurityError(EnvironmentError):
    """Error related to security checks."""
    pass

class EnvironmentManager:
    """Manages the Python environment and dependencies for ELLMa."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize the environment manager.
        
        Args:
            project_root: Path to the project root. If None, will use the parent of this file.
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.pyproject_path = self.project_root / 'pyproject.toml'
        self.poetry_lock = self.project_root / 'poetry.lock'
        self.venv_path = self._find_venv()
        self.is_venv = self.venv_path is not None
        
    def _find_venv(self) -> Optional[Path]:
        """Find the virtual environment path."""
        # Check common venv locations
        possible_paths = [
            self.project_root / 'venv',
            self.project_root / '.venv',
            Path(sys.prefix),
        ]
        
        for path in possible_paths:
            if (path / 'pyvenv.cfg').exists() or (path / 'bin' if os.name != 'nt' else path / 'Scripts'):
                return path
        return None
    
    def check_environment(self) -> EnvironmentCheck:
        """Check if the current environment is properly set up."""
        try:
            # Check Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            
            # Check if in virtual environment
            if not self.is_venv:
                return EnvironmentCheck(
                    status=EnvironmentStatus.NOT_IN_VENV,
                    error="Not running in a virtual environment"
                )
            
            # Check Poetry is installed
            try:
                importlib.import_module('poetry')
            except ImportError:
                return EnvironmentCheck(
                    status=EnvironmentStatus.MISSING_POETRY,
                    error="Poetry is not installed"
                )
            
            # Check dependencies
            missing_deps = self._check_dependencies()
            if missing_deps:
                return EnvironmentCheck(
                    status=EnvironmentStatus.MISSING_DEPS,
                    missing_deps=missing_deps,
                    error=f"Missing dependencies: {', '.join(missing_deps)}"
                )
            
            return EnvironmentCheck(status=EnvironmentStatus.VALID)
            
        except Exception as e:
            return EnvironmentCheck(
                status=EnvironmentStatus.POETRY_ERROR,
                error=f"Error checking environment: {str(e)}"
            )
    
    def _check_dependencies(self) -> List[str]:
        """Check if all required dependencies are installed."""
        try:
            # Read pyproject.toml to get dependencies
            import tomli
            
            with open(self.pyproject_path, 'rb') as f:
                pyproject = tomli.load(f)
            
            # Get dependencies from pyproject.toml
            dependencies = pyproject.get('tool', {}).get('poetry', {}).get('dependencies', {})
            required = {name.lower() for name in dependencies.keys() if name != 'python'}
            
            # Get installed packages
            installed = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
            
            # Find missing
            return [pkg for pkg in required if pkg not in installed]
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return ["error_checking_dependencies"]
    
    def install_dependencies(self, group: str = None) -> bool:
        """Install project dependencies using Poetry.
        
        Args:
            group: Optional dependency group to install (e.g., 'dev', 'audio')
            
        Returns:
            bool: True if installation was successful
        """
        try:
            cmd = ["poetry", "install"]
            if group:
                cmd.extend(["--with", group])
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True
            )
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing dependencies: {e}")
            return False
    
    def ensure_environment(self, auto_repair: bool = True) -> bool:
        """Ensure the environment is properly set up.
        
        Args:
            auto_repair: If True, attempt to fix issues automatically
            
        Returns:
            bool: True if environment is valid or was successfully repaired
        """
        check = self.check_environment()
        
        if check.status == EnvironmentStatus.VALID:
            return True
            
        if not auto_repair:
            return False
            
        # Attempt to repair
        if check.status == EnvironmentStatus.MISSING_DEPS:
            logger.info("Installing missing dependencies...")
            return self.install_dependencies()
            
        elif check.status == EnvironmentStatus.NOT_IN_VENV:
            logger.warning("Not running in a virtual environment. Please activate one first.")
            return False
            
        elif check.status == EnvironmentStatus.MISSING_POETRY:
            logger.warning("Poetry is required for dependency management. Please install it first.")
            return False
            
        return False

# Global instance
env_manager = EnvironmentManager()

def ensure_environment(auto_repair: bool = True) -> bool:
    """Ensure the environment is properly set up."""
    return env_manager.ensure_environment(auto_repair=auto_repair)

def install_dependencies(group: str = None) -> bool:
    """Install project dependencies."""
    return env_manager.install_dependencies(group=group)

def check_environment() -> EnvironmentCheck:
    """Check the current environment status."""
    return env_manager.check_environment()
