"""
ELLMa Core Module

This module contains the core functionality of ELLMa including
the main agent, evolution engine, and shell interface.
"""

from ellma.core.agent import ELLMa
from ellma.core.evolution import EvolutionEngine
from ellma.core.shell import InteractiveShell

__all__ = [
    'ELLMa',
    'EvolutionEngine',
    'InteractiveShell'
]