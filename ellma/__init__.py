"""
ELLMa - Evolutionary Local LLM Agent

A self-evolving AI assistant that improves itself through usage and experience.
"""

__version__ = "0.1.6"
__author__ = "ELLMa Team"
__email__ = "contact@ellma.dev"
__license__ = "MIT"

# Import security module early to ensure environment is properly set up
# Skip checks if we're in setup.py or during package installation
if not any('setup.py' in arg for arg in __import__('sys').argv):
    try:
        from ellma.security import ensure_environment
        ensure_environment(auto_repair=True)
    except ImportError as e:
        import warnings
        warnings.warn(f"Failed to initialize security module: {e}")
    except Exception as e:
        import warnings
        warnings.warn(f"Error during security initialization: {e}")

# Common exceptions first to avoid circular imports
class ELLMaError(Exception):
    """Base exception for ELLMa"""
    pass


class ModelNotFoundError(ELLMaError):
    """Raised when LLM model is not found"""
    pass


class ModuleLoadError(ELLMaError):
    """Raised when module loading fails"""
    pass


class EvolutionError(ELLMaError):
    """Raised when evolution process fails"""
    pass


class CommandError(ELLMaError):
    """Raised when command execution fails"""
    pass


# Core imports for easy access
from ellma.core.agent import ELLMa
from ellma.core.evolution import EvolutionEngine
from ellma.core.shell import InteractiveShell


# Version info
VERSION_INFO = tuple(map(int, __version__.split('.')))

# Public API
__all__ = [
    'ELLMa',
    'EvolutionEngine',
    'InteractiveShell',
    'ELLMaError',
    'ModelNotFoundError',
    'ModuleLoadError',
    'EvolutionError',
    'CommandError',
    '__version__',
    'BANNER',
]

# Package metadata for introspection
PACKAGE_INFO = {
    'name': 'ellma',
    'version': __version__,
    'description': 'Evolutionary Local LLM Agent - Self-improving AI assistant',
    'author': __author__,
    'email': __email__,
    'license': __license__,
    'url': 'https://github.com/wronai/ellma',
    'keywords': ['llm', 'ai', 'agent', 'automation', 'evolution'],
}


def get_version():
    """Get package version string"""
    return __version__


def get_package_info():
    """Get package information dictionary"""
    return PACKAGE_INFO.copy()


# Import BANNER from constants module
from ellma.constants import BANNER