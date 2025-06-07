"""
ELLMa Evolution Package

This package contains the core evolution engine that enables ELLMa to
analyze its performance, identify improvement opportunities, and
automatically generate new capabilities.

Public API:
    EvolutionEngine - Main engine class for managing the evolution process
    EvolutionConfig - Configuration for evolution parameters
    Population - Manages a population of candidate solutions
    
    Selection Operators:
        tournament_selection - Select candidates using tournament selection
        rank_selection - Select candidates using rank-based selection
        elitism_selection - Select top candidates using elitism
        roulette_wheel_selection - Select candidates using fitness-proportionate selection
        stochastic_universal_sampling - Select multiple candidates using SUS
    
    Crossover Operators:
        single_point_crossover - Single-point crossover
        uniform_crossover - Uniform crossover
        subtree_crossover - Subtree crossover for tree-based representations
        arithmetic_crossover - Arithmetic crossover for real-valued representations
    
    Mutation Operators:
        gaussian_mutation - Add Gaussian noise to numeric values
        bit_flip_mutation - Flip bits in binary representations
        subtree_mutation - Replace a subtree in tree-based representations
        swap_mutation - Swap two values in the individual
"""

# Core components
from .engine import EvolutionEngine
from .config import EvolutionConfig
from .population import Population

# Selection operators
from .selection import (
    tournament_selection,
    rank_selection,
    elitism_selection,
    roulette_wheel_selection,
    stochastic_universal_sampling,
    create_mating_pool
)

# Crossover operators
from .crossover import (
    single_point_crossover,
    uniform_crossover,
    subtree_crossover,
    arithmetic_crossover,
    get_crossover_method
)

# Mutation operators
from .mutation import (
    gaussian_mutation,
    bit_flip_mutation,
    subtree_mutation,
    swap_mutation,
    get_mutation_method
)

# Exceptions
from .exceptions import (
    EvolutionError,
    ResourceLimitExceeded,
    EvolutionTimeout,
    InvalidEvolutionState,
    ModuleGenerationError,
    TestFailure
)

# Utilities
from .utils import (
    setup_evolution_environment,
    check_system_resources,
    cleanup_resources,
    log_evolution_result,
    time_execution,
    with_retry,
    get_progress_bar,
    validate_module_code
)

__all__ = [
    # Core components
    'EvolutionEngine',
    'EvolutionConfig',
    'Population',
    
    # Selection operators
    'tournament_selection',
    'rank_selection',
    'elitism_selection',
    'roulette_wheel_selection',
    'stochastic_universal_sampling',
    'create_mating_pool',
    
    # Crossover operators
    'single_point_crossover',
    'uniform_crossover',
    'subtree_crossover',
    'arithmetic_crossover',
    'get_crossover_method',
    
    # Mutation operators
    'gaussian_mutation',
    'bit_flip_mutation',
    'subtree_mutation',
    'swap_mutation',
    'get_mutation_method',
    
    # Exceptions
    'EvolutionError',
    'ResourceLimitExceeded',
    'EvolutionTimeout',
    'InvalidEvolutionState',
    'ModuleGenerationError',
    'TestFailure',
    
    # Utilities
    'setup_evolution_environment',
    'check_system_resources',
    'cleanup_resources',
    'log_evolution_result',
    'time_execution',
    'with_retry',
    'get_progress_bar',
    'validate_module_code'
]
