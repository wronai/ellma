"""
ELLMa Security and Dependency Management Layer

This module provides a security wrapper around ELLMa that handles:
- Virtual environment management
- Dependency installation and repair
- Environment validation
- Security checks
- File and directory permission validation
- Network access controls
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

from .validation import (
    SecurityValidator,
    SecurityFinding,
    SecurityCheckSeverity,
    validate_security,
    get_security_findings,
    clear_security_findings
)

__all__ = [
    # Core functionality
    'ensure_environment',
    'install_dependencies',
    'check_environment',
    # Core exceptions
    'EnvironmentError',
    'DependencyError',
    'SecurityError',
    # Core types
    'EnvironmentStatus',
    'EnvironmentCheck',
    # Validation functionality
    'SecurityValidator',
    'SecurityFinding',
    'SecurityCheckSeverity',
    'validate_security',
    'get_security_findings',
    'clear_security_findings'
]
