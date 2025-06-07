"""
Evolution Configuration

This module defines the configuration for the evolution process.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any


@dataclass
class EvolutionConfig:
    """Configuration for the evolution process.
    
    Attributes:
        max_generations: Maximum number of generations to evolve
        population_size: Number of candidates in each generation
        mutation_rate: Probability of mutation (0.0 to 1.0)
        crossover_rate: Probability of crossover (0.0 to 1.0)
        elitism: Number of top candidates to preserve between generations
        timeout: Maximum time to allow for evolution
        working_dir: Directory for evolution artifacts
        allowed_modules: Set of modules that can be imported during evolution
        max_module_size: Maximum size of generated modules in bytes
        max_memory_mb: Maximum memory usage in MB
        max_cpu_percent: Maximum CPU percentage to use
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'max_generations': self.max_generations,
            'population_size': self.population_size,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'elitism': self.elitism,
            'timeout_seconds': self.timeout.total_seconds(),
            'working_dir': str(self.working_dir),
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
