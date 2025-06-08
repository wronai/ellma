"""
ELLMa Code Generators Module

This module contains code generators for various programming languages
and configuration formats.
"""

from ellma.generators.bash import BashGenerator
from ellma.generators.python import PythonGenerator

__all__ = [
    'BashGenerator',
    'PythonGenerator'
]

# Generator registry
GENERATORS = {
    'bash': BashGenerator,
    'python': PythonGenerator
}

def get_generator(language: str, agent):
    """Get generator for specified language"""
    generator_class = GENERATORS.get(language.lower())
    if generator_class:
        return generator_class(agent)
    else:
        raise ValueError(f"Generator for '{language}' not found")