"""
Population Management

This module handles the creation, maintenance, and evolution of the population
of candidate solutions in the evolution process.
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging

from .exceptions import EvolutionError
from .config import EvolutionConfig
from .selection import (
    tournament_selection,
    rank_selection,
    elitism_selection,
    roulette_wheel_selection,
    stochastic_universal_sampling,
    create_mating_pool
)
from .crossover import single_point_crossover, uniform_crossover, get_crossover_method
from .mutation import gaussian_mutation, bit_flip_mutation, get_mutation_method

logger = logging.getLogger(__name__)

@dataclass
class Population:
    """Manages a population of candidate solutions."""
    
    config: EvolutionConfig
    individuals: List[Dict[str, Any]] = field(default_factory=list)
    generation: int = 0
    best_individual: Optional[Dict[str, Any]] = None
    best_fitness: float = float('-inf')
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize the population."""
        if not self.individuals:
            self.initialize()
    
    def initialize(self) -> None:
        """Initialize the population with random individuals."""
        self.individuals = [self._create_individual() 
                          for _ in range(self.config.population_size)]
        self.generation = 0
        self.best_individual = None
        self.best_fitness = float('-inf')
        self.history = []
    
    def _create_individual(self) -> Dict[str, Any]:
        """Create a new individual with random values."""
        # This is a simple example - override in subclasses for specific representations
        return {
            'genome': np.random.random(10).tolist(),  # Example: 10-dimensional vector
            'fitness': None,
            'age': 0,
            'parent_ids': []
        }
    
    def evaluate(self, fitness_func: Callable) -> None:
        """Evaluate all individuals in the population.
        
        Args:
            fitness_func: Function that takes an individual and returns its fitness
        """
        for individual in self.individuals:
            if individual['fitness'] is None:
                individual['fitness'] = fitness_func(individual)
                individual['age'] += 1
    
    def evolve(self) -> None:
        """Perform one generation of evolution."""
        if not self.individuals:
            raise EvolutionError("Cannot evolve an empty population")
            
        # Select parents
        parents = self._select_parents()
        
        # Create offspring through crossover and mutation
        offspring = []
        
        while len(offspring) < len(self.individuals):
            # Select two parents
            parent1, parent2 = random.sample(parents, 2)
            
            # Crossover
            if random.random() < self.config.crossover_rate:
                # Get crossover method (simplified - could be configurable)
                crossover_func = get_crossover_method('single_point')
                result = crossover_func(parent1, parent2)
                
                if result.success:
                    child1, child2 = result.offspring1, result.offspring2
                    
                    # Mutate
                    mutation_func = get_mutation_method('gaussian')
                    child1 = mutation_func(child1, mutation_rate=0.1).individual
                    child2 = mutation_func(child2, mutation_rate=0.1).individual
                    
                    # Reset fitness
                    child1['fitness'] = None
                    child2['fitness'] = None
                    
                    # Track parentage
                    child1['parent_ids'] = [id(parent1), id(parent2)]
                    child2['parent_ids'] = [id(parent1), id(parent2)]
                    
                    offspring.extend([child1, child2])
        
        # Replace population (elitism)
        if self.config.elitism > 0:
            elites = elitism_selection(
                self.individuals, 
                min(self.config.elitism, len(self.individuals) // 2)
            )
            offspring = elites + offspring
        
        # Keep population size constant
        self.individuals = offspring[:self.config.population_size]
        self.generation += 1
        
        # Update best individual
        self._update_best()
        
        # Record history
        self._record_generation()
    
    def _select_parents(self) -> List[Dict[str, Any]]:
        """Select parents for reproduction."""
        # Use tournament selection by default
        return [
            tournament_selection(self.individuals, tournament_size=3)
            for _ in range(len(self.individuals))
        ]
    
    def _update_best(self) -> None:
        """Update the best individual found so far."""
        if not self.individuals:
            return
            
        current_best = max(self.individuals, key=lambda x: x.get('fitness', float('-inf')))
        current_fitness = current_best.get('fitness', float('-inf'))
        
        if current_fitness > self.best_fitness:
            self.best_fitness = current_fitness
            self.best_individual = current_best.copy()
    
    def _record_generation(self) -> None:
        """Record statistics about the current generation."""
        if not self.individuals:
            return
            
        fitnesses = [ind.get('fitness', 0) for ind in self.individuals]
        
        stats = {
            'generation': self.generation,
            'best_fitness': max(fitnesses),
            'worst_fitness': min(fitnesses),
            'avg_fitness': sum(fitnesses) / len(fitnesses),
            'median_fitness': sorted(fitnesses)[len(fitnesses)//2],
            'std_fitness': np.std(fitnesses) if len(fitnesses) > 1 else 0,
            'population_size': len(self.individuals),
            'best_individual': self.best_individual.copy() if self.best_individual else None
        }
        
        self.history.append(stats)
        logger.debug(f"Generation {self.generation}: "
                   f"Best={stats['best_fitness']:.4f}, "
                   f"Avg={stats['avg_fitness']:.4f}")
    
    def save_state(self, path: Path) -> None:
        """Save the current population state to a file.
        
        Args:
            path: Path to save the state file
        """
        state = {
            'config': self.config.to_dict(),
            'individuals': self.individuals,
            'generation': self.generation,
            'best_individual': self.best_individual,
            'best_fitness': self.best_fitness,
            'history': self.history
        }
        
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def load_state(cls, path: Path) -> 'Population':
        """Load a population from a saved state file.
        
        Args:
            path: Path to the saved state file
            
        Returns:
            A Population instance loaded from the file
        """
        with open(path, 'r') as f:
            state = json.load(f)
        
        config = EvolutionConfig.from_dict(state['config'])
        population = cls(config=config)
        
        population.individuals = state['individuals']
        population.generation = state['generation']
        population.best_individual = state['best_individual']
        population.best_fitness = state['best_fitness']
        population.history = state['history']
        
        return population
