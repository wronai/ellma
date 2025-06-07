"""
Evolution Exceptions

This module defines custom exceptions for the evolution system.
"""

class EvolutionError(Exception):
    """Base exception for evolution-related errors."""
    pass

class ResourceLimitExceeded(EvolutionError):
    """Raised when evolution exceeds resource limits."""
    pass

class EvolutionTimeout(EvolutionError):
    """Raised when evolution process times out."""
    pass

class InvalidEvolutionState(EvolutionError):
    """Raised when evolution is in an invalid state for the requested operation."""
    pass

class ModuleGenerationError(EvolutionError):
    """Raised when module generation fails."""
    pass

class TestFailure(EvolutionError):
    """Raised when evolution tests fail."""
    pass
