"""
Evolution Configuration

This module defines the configuration for the evolution process, including validation
of all configuration parameters to ensure they are within acceptable ranges.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union

class ConfigurationError(ValueError):
    """Raised when a configuration value is invalid."""
    pass

def validate_positive_int(value: int, name: str) -> None:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{name} must be a positive integer, got {value}")

def validate_probability(value: float, name: str) -> None:
    """Validate that a value is a valid probability (0.0 to 1.0)."""
    if not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ConfigurationError(f"{name} must be a float between 0.0 and 1.0, got {value}")

def validate_timeout(value: Union[timedelta, int, float]) -> timedelta:
    """Validate and normalize the timeout value.
    
    Args:
        value: Timeout value as timedelta, or seconds (int/float)
        
    Returns:
        Normalized timedelta object
        
    Raises:
        ConfigurationError: If the timeout is invalid
    """
    if isinstance(value, (int, float)) and value > 0:
        return timedelta(seconds=value)
    elif isinstance(value, timedelta) and value.total_seconds() > 0:
        return value
    raise ConfigurationError("timeout must be a positive timedelta or number of seconds")


@dataclass
class EvolutionConfig:
    """Configuration for the evolution process.
    
    This class holds all configuration parameters for the evolutionary algorithm,
    with sensible defaults and validation to ensure all values are within
    acceptable ranges.
    
    Args:
        max_generations: Maximum number of generations to evolve (positive integer)
        population_size: Number of candidates in each generation (positive integer)
        mutation_rate: Probability of mutation (0.0 to 1.0)
        crossover_rate: Probability of crossover (0.0 to 1.0)
        elitism: Number of top candidates to preserve between generations
        timeout: Maximum time to allow for evolution (positive timedelta)
        working_dir: Directory for evolution artifacts (Path or str)
        allowed_modules: Set of modules that can be imported during evolution
        max_module_size: Maximum size of generated modules in bytes (positive int)
        max_memory_mb: Maximum memory usage in MB (positive int)
        max_cpu_percent: Maximum CPU percentage to use (1-100)
        
    Raises:
        ConfigurationError: If any parameter is outside its valid range
    """
    max_generations: int = 10
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elitism: int = 2
    timeout: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    working_dir: Path = field(default_factory=lambda: Path.cwd() / "evolution")
    allowed_modules: Set[str] = field(default_factory=set)
    max_module_size: int = 1024 * 1024  # 1MB
    max_memory_mb: int = 4096  # 4GB
    max_cpu_percent: int = 80  # 80% CPU
    
    def __post_init__(self):
        """Validate all configuration parameters after initialization."""
        # Validate integer parameters
        for name in ['max_generations', 'population_size', 'elitism', 'max_module_size', 'max_memory_mb']:
            validate_positive_int(getattr(self, name), name)
            
        # Validate probabilities
        validate_probability(self.mutation_rate, 'mutation_rate')
        validate_probability(self.crossover_rate, 'crossover_rate')
        
        # Validate and normalize timeout
        self.timeout = validate_timeout(self.timeout)
        
        # Validate CPU percentage
        if not (0 < self.max_cpu_percent <= 100):
            raise ConfigurationError("max_cpu_percent must be between 1 and 100")
            
        # Ensure working_dir is a Path object
        if not isinstance(self.working_dir, Path):
            self.working_dir = Path(self.working_dir)
            
        # Ensure allowed_modules is a set
        if not isinstance(self.allowed_modules, set):
            if isinstance(self.allowed_modules, (list, tuple)):
                self.allowed_modules = set(self.allowed_modules)
            else:
                self.allowed_modules = set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary.
        
        Returns:
            Dict containing all configuration parameters with serializable values
            
        Example:
            >>> config = EvolutionConfig()
            >>> config_dict = config.to_dict()
            >>> 'max_generations' in config_dict
            True
        """
        return {
            'max_generations': self.max_generations,
            'population_size': self.population_size,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'elitism': self.elitism,
            'timeout_seconds': self.timeout.total_seconds(),
            'working_dir': str(self.working_dir.absolute()),
            'allowed_modules': list(self.allowed_modules),
            'max_module_size': self.max_module_size,
            'max_memory_mb': self.max_memory_mb,
            'max_cpu_percent': self.max_cpu_percent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionConfig':
        """Create config from dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                if key == 'timeout_seconds':
                    setattr(config, 'timeout', timedelta(seconds=value))
                elif key == 'working_dir':
                    setattr(config, key, Path(value))
                elif key == 'allowed_modules':
                    setattr(config, key, set(value))
                else:
                    setattr(config, key, value)
        return config
