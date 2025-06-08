"""
Utilities for managing the evolution process and system resources.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EvolutionConfig:
    """Configuration for the evolution process."""
    
    DEFAULTS = {
        'max_threads': 4,
        'memory_limit_mb': 4096,
        'max_evolution_time': 300,  # 5 minutes
        'enable_parallel': True,
        'max_module_size_mb': 10,
        'enable_docker': True,
        'enable_rollback': True
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration overrides."""
        self.config = self.DEFAULTS.copy()
        if config:
            self.config.update(config)
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to config values."""
        if name in self.config:
            return self.config[name]
        raise AttributeError(f"No such configuration: {name}")
    
    def validate(self) -> bool:
        """Validate the configuration."""
        try:
            assert self.max_threads > 0, "max_threads must be positive"
            assert self.memory_limit_mb > 0, "memory_limit_mb must be positive"
            return True
        except AssertionError as e:
            logger.error(f"Invalid configuration: {e}")
            return False


def setup_evolution_environment(config: Optional[Dict[str, Any]] = None) -> EvolutionConfig:
    """
    Set up the environment for evolution.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        EvolutionConfig: The configuration being used
    """
    # Create config with overrides
    evolution_config = EvolutionConfig(config)
    
    # Set environment variables for threading
    os.environ['OMP_NUM_THREADS'] = str(min(evolution_config.max_threads, os.cpu_count() or 1))
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log configuration
    logger.info("Evolution environment configured")
    for k, v in evolution_config.config.items():
        logger.debug(f"  {k}: {v}")
    
    return evolution_config


def check_system_resources(config: EvolutionConfig) -> Dict[str, Any]:
    """
    Check if system has enough resources for evolution.
    
    Args:
        config: Evolution configuration
        
    Returns:
        Dict with resource information and availability status
    """
    try:
        import psutil
        
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_available = cpu_percent < 90  # Assume <90% CPU usage is available
        
        disk_usage = psutil.disk_usage('/')
        disk_available = disk_usage.percent < 90  # <90% disk usage
        
        has_resources = all([
            available_mb > config.memory_limit_mb,
            cpu_available,
            disk_available
        ])
        
        return {
            'has_resources': has_resources,
            'memory': {
                'available_mb': available_mb,
                'required_mb': config.memory_limit_mb,
                'sufficient': available_mb > config.memory_limit_mb
            },
            'cpu': {
                'percent': cpu_percent,
                'available': cpu_available
            },
            'disk': {
                'percent': disk_usage.percent,
                'available': disk_available
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return {
            'has_resources': False,
            'error': str(e)
        }


def cleanup_resources() -> None:
    """Clean up resources after evolution."""
    try:
        import gc
        import torch
        
        # Clear PyTorch cache if available
        if 'torch' in sys.modules:
            torch.cuda.empty_cache()
        
        # Run garbage collection
        gc.collect()
        
    except Exception as e:
        logger.warning(f"Error during resource cleanup: {e}")


def log_evolution_result(result: Dict[str, Any], log_dir: Path) -> None:
    """
    Log the result of an evolution cycle.
    
    Args:
        result: Dictionary containing evolution results
        log_dir: Directory to store logs
    """
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = result.get('timestamp', 'unknown')
        log_file = log_dir / f"evolution_{timestamp}.json"
        
        with open(log_file, 'w') as f:
            import json
            json.dump(result, f, indent=2)
            
        logger.info(f"Evolution results logged to {log_file}")
        
    except Exception as e:
        logger.error(f"Failed to log evolution result: {e}")
