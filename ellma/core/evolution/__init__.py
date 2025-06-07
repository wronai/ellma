"""
ELLMa Evolution Package

This package contains the core evolution engine that enables ELLMa to
analyze its performance, identify improvement opportunities, and
automatically generate new capabilities.

Public API:
    EvolutionEngine - Main engine class for managing the evolution process
    EvolutionConfig - Configuration for evolution parameters
    EvolutionError - Base exception for evolution-related errors
"""

from .engine import EvolutionEngine
from .config import EvolutionConfig
from .exceptions import EvolutionError

__all__ = [
    'EvolutionEngine',
    'EvolutionConfig',
    'EvolutionError'
]
