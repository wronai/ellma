"""
Data manipulation utility functions.
"""

from typing import Dict, Any, List, TypeVar, AnyStr
import re

T = TypeVar('T')

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten nested dictionary

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Key separator

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split list into chunks of specified size

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case to camelCase

    Args:
        snake_str: Snake case string

    Returns:
        Camel case string
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase to snake_case

    Args:
        camel_str: Camel case string

    Returns:
        Snake case string
    """
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()

def parse_size_string(size_str: str) -> int:
    """
    Parse size string to bytes

    Args:
        size_str: Size string like "10MB", "1.5GB"

    Returns:
        Size in bytes
    """
    size_str = size_str.strip().upper()
    if not size_str:
        return 0
    
    # Extract number and unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTP]?B?)?$', size_str)
    if not match:
        raise ValueError(f"Invalid size string: {size_str}")
    
    num = float(match.group(1))
    unit = match.group(2) or 'B'
    
    # Convert to bytes
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        'PB': 1024 ** 5,
        'K': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3,
        'T': 1024 ** 4,
        'P': 1024 ** 5
    }
    
    if unit not in units:
        raise ValueError(f"Unknown unit: {unit}")
    
    return int(num * units[unit])
