"""
ELLMa Helper Utilities

This package contains common helper functions and utilities organized into logical modules.

For backward compatibility, all functions are still available directly from this package.
New code should import from the specific submodules directly for better organization.
"""

import sys
import warnings
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from pathlib import Path

# Import all functions from submodules
from .file_utils import (
    ensure_directory,
    get_file_hash,
    get_file_size_human,
    create_temp_file,
    cleanup_temp_files,
    is_newer_than
)

from .network_utils import (
    is_port_open,
    wait_for_port,
    get_free_port
)

from .decorators import (
    timeout_decorator,
    retry_decorator,
    memoize_decorator,
    debounce,
    throttle
)

from .data_utils import (
    deep_merge_dicts,
    flatten_dict,
    chunk_list,
    snake_to_camel,
    camel_to_snake,
    parse_size_string
)

from .validation import (
    validate_email,
    validate_url,
    validate_ip_address,
    validate_regex,
    validate_file_exists,
    validate_directory,
    validate_type
)

from .time_utils import (
    get_timestamp,
    parse_timestamp,
    days_ago,
    format_duration,
    time_since,
    is_weekday
)

from .concurrency import (
    RateLimiter,
    CircuitBreaker,
    TaskPool
)

# Re-export all public functions and classes
__all__ = [
    # File utilities
    'ensure_directory',
    'get_file_hash',
    'get_file_size_human',
    'create_temp_file',
    'cleanup_temp_files',
    'is_newer_than',
    
    # Network utilities
    'is_port_open',
    'wait_for_port',
    'get_free_port',
    
    # Decorators
    'timeout_decorator',
    'retry_decorator',
    'memoize_decorator',
    'debounce',
    'throttle',
    
    # Data utilities
    'deep_merge_dicts',
    'flatten_dict',
    'chunk_list',
    'snake_to_camel',
    'camel_to_snake',
    'parse_size_string',
    
    # Validation
    'validate_email',
    'validate_url',
    'validate_ip_address',
    'validate_regex',
    'validate_file_exists',
    'validate_directory',
    'validate_type',
    
    # Time utilities
    'get_timestamp',
    'parse_timestamp',
    'days_ago',
    'format_duration',
    'time_since',
    'is_weekday',
    
    # Concurrency
    'RateLimiter',
    'CircuitBreaker',
    'TaskPool'
]

# Issue deprecation warning for direct imports
warnings.warn(
    "Direct imports from ellma.utils.helpers are deprecated. "
    "Please import from specific submodules (e.g., ellma.utils.helpers.file_utils).",
    DeprecationWarning,
    stacklevel=2
)
