"""
Tests for the EvolutionConfig class.
"""

import pytest
from datetime import timedelta
from pathlib import Path

from ellma.core.evolution.config import EvolutionConfig, ConfigurationError

def test_default_config():
    """Test that default configuration values are set correctly."""
    config = EvolutionConfig()
    
    assert config.max_generations == 10
    assert config.population_size == 50
    assert config.mutation_rate == 0.1
    assert config.crossover_rate == 0.7
    assert config.elitism == 2
    assert config.max_module_size == 1024 * 1024  # 1MB
    assert config.max_memory_mb == 4096  # 4GB
    assert config.max_cpu_percent == 80  # 80%
    assert config.timeout == timedelta(minutes=30)
    assert config.working_dir == Path.cwd() / "evolution"
    assert config.allowed_modules == set()

def test_validation():
    """Test validation of configuration parameters."""
    # Test valid configuration
    valid_config = EvolutionConfig(
        max_generations=5,
        population_size=20,
        mutation_rate=0.2,
        crossover_rate=0.8,
        elitism=1,
        timeout=timedelta(minutes=10),
        working_dir="/tmp/evolution",
        max_module_size=512 * 1024,
        max_memory_mb=2048,
        max_cpu_percent=90,
    )
    assert valid_config is not None
    
    # Test invalid values
    with pytest.raises(ConfigurationError):
        EvolutionConfig(max_generations=0)  # Must be positive
    
    with pytest.raises(ConfigurationError):
        EvolutionConfig(mutation_rate=1.1)  # Must be <= 1.0
    
    with pytest.raises(ConfigurationError):
        EvolutionConfig(timeout=timedelta(seconds=0))  # Must be positive
    
    with pytest.raises(ConfigurationError):
        EvolutionConfig(max_cpu_percent=0)  # Must be between 1-100

def test_to_dict():
    """Test conversion to dictionary."""
    config = EvolutionConfig()
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert config_dict['max_generations'] == 10
    assert config_dict['mutation_rate'] == 0.1
    assert 'allowed_modules' in config_dict
    assert isinstance(config_dict['allowed_modules'], list)

def test_working_dir_conversion():
    """Test that working_dir is converted to Path if passed as string."""
    config = EvolutionConfig(working_dir="/tmp/test_evolution")
    assert isinstance(config.working_dir, Path)
    assert str(config.working_dir) == "/tmp/test_evolution"
    
    # Test that Path objects are preserved
    path_obj = Path("/another/path")
    config = EvolutionConfig(working_dir=path_obj)
    assert config.working_dir is path_obj
