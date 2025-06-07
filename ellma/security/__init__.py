"""
ELLMa Security and Dependency Management Layer

This module provides a security wrapper around ELLMa that handles:
- Virtual environment management
- Dependency installation and repair
- Environment validation
- Security checks
"""

from .core import (
    ensure_environment,
    install_dependencies,
    check_environment,
    EnvironmentError,
    DependencyError,
    SecurityError,
    EnvironmentStatus,
    EnvironmentCheck
)

__all__ = [
    'ensure_environment',
    'install_dependencies',
    'check_environment',
    'EnvironmentError',
    'DependencyError',
    'SecurityError',
    'EnvironmentStatus',
    'EnvironmentCheck'
]
