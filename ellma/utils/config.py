"""
Configuration management for ELLMa.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Type
from typing_extensions import Self

T = TypeVar('T', bound='ConfigManager')

class ConfigManager:
    """
    A class to manage configuration settings with file persistence.
    
    This class handles loading, saving, and accessing configuration settings
    from a JSON file. It supports nested dictionaries and provides type hints.
    """
    
    def __init__(self, config_path: Optional[str] = None, defaults: Optional[Dict[str, Any]] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Path to the configuration file. If None, uses a default path.
            defaults: Default configuration values.
        """
        self.defaults = defaults or {}
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self._data: Dict[str, Any] = {}
        self.load()
    
    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".config" / "ellma"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            else:
                self._data = self.defaults.copy()
                self.save()
        except (json.JSONDecodeError, OSError) as e:
            self._data = self.defaults.copy()
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except OSError as e:
            raise RuntimeError(f"Failed to save config to {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-separated key path (e.g., 'database.host')
            default: Default value if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        keys = key.split('.')
        value = self._data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Try to get from defaults if available
            if default is not None:
                return default
            return self._get_nested_default(keys)
    
    def _get_nested_default(self, keys: list[str]) -> Any:
        """Get a value from defaults using nested keys."""
        value = self.defaults
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated key path
            value: Value to set
            save: Whether to save the configuration to file immediately
        """
        keys = key.split('.')
        d = self._data
        
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        
        d[keys[-1]] = value
        
        if save:
            self.save()
    
    def update(self, data: Dict[str, Any], save: bool = True) -> None:
        """
        Update multiple configuration values at once.
        
        Args:
            data: Dictionary of key-value pairs to update
            save: Whether to save the configuration to file immediately
        """
        for key, value in data.items():
            self.set(key, value, save=False)
        
        if save:
            self.save()
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dict-style access."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a configuration value using dict-style access."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if a configuration key exists."""
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self._data.copy()
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any], config_path: Optional[str] = None) -> T:
        """
        Create a ConfigManager from a dictionary.
        
        Args:
            data: Configuration data
            config_path: Path to save the configuration
            
        Returns:
            A new ConfigManager instance
        """
        instance = cls(config_path=config_path, defaults={})
        instance._data = data
        return instance
