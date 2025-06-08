"""
Selection Operators

This module implements various selection strategies for the evolution process.
"""

import random
from typing import List, Dict, Any, Callable, Tuple
import numpy as np


def tournament_selection(population: List[Dict[str, Any]], 
                        tournament_size: int = 3) -> Dict[str, Any]:
    """Select a candidate using tournament selection.
    
    Args:
        population: List of candidate solutions with fitness scores
        tournament_size: Number of candidates to compete in each tournament
        
    Returns:
        The selected candidate
    """
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda x: x['fitness'])


def rank_selection(population: List[Dict[str, Any]], 
                   selection_pressure: float = 1.5) -> Dict[str, Any]:
    """Select a candidate using rank-based selection.
    
    Args:
        population: List of candidate solutions with fitness scores
        selection_pressure: Pressure of selection (1.0 < pressure <= 2.0)
        
    Returns:
        The selected candidate
    """
    # Sort population by fitness
    sorted_pop = sorted(population, key=lambda x: x['fitness'])
    
    # Assign ranks (1 to N)
    ranks = np.arange(1, len(sorted_pop) + 1)
    
    # Calculate selection probabilities
    # Using linear ranking selection
    min_prob = 2 - selection_pressure
    max_prob = 2 * (selection_pressure - 1)
    probs = (min_prob + (max_prob - min_prob) * (ranks - 1) / (len(ranks) - 1)) / len(ranks)
    
    # Select based on rank probabilities
    return np.random.choice(sorted_pop, p=probs)


def elitism_selection(population: List[Dict[str, Any]], 
                     elitism_count: int) -> List[Dict[str, Any]]:
    """Select the top N candidates using elitism.
    
    Args:
        population: List of candidate solutions with fitness scores
        elitism_count: Number of top candidates to select
        
    Returns:
        List of selected elite candidates
    """
    return sorted(population, key=lambda x: x['fitness'], reverse=True)[:elitism_count]


def roulette_wheel_selection(population: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Select a candidate using fitness-proportionate selection.
    
    Args:
        population: List of candidate solutions with fitness scores
        
    Returns:
        The selected candidate
    """
    total_fitness = sum(max(0, c['fitness']) for c in population)
    if total_fitness <= 0:
        return random.choice(population)
        
    pick = random.uniform(0, total_fitness)
    current = 0
    for candidate in population:
        current += max(0, candidate['fitness'])
        if current > pick:
            return candidate
    return population[-1]


def stochastic_universal_sampling(
    population: List[Dict[str, Any]],
    count: int
) -> List[Dict[str, Any]]:
    """Select multiple candidates using stochastic universal sampling.
    
    Args:
        population: List of candidate solutions with fitness scores
        count: Number of candidates to select
        
    Returns:
        List of selected candidates
    """
    # Calculate total fitness
    total_fitness = sum(max(0, c['fitness']) for c in population)
    if total_fitness <= 0:
        return random.sample(population, min(count, len(population)))
    
    # Calculate point distances
    pointers = []
    distance = total_fitness / count
    start = random.uniform(0, distance)
    
    for i in range(count):
        pointers.append(start + i * distance)
    
    # Select candidates
    selected = []
    current_sum = 0
    i = 0
    
    for candidate in sorted(population, key=lambda x: x['fitness']):
        current_sum += max(0, candidate['fitness'])
        while i < len(pointers) and pointers[i] <= current_sum:
            selected.append(candidate)
            i += 1
            if i >= len(pointers):
                break
    
    return selected


def create_mating_pool(
    population: List[Dict[str, Any]],
    pool_size: int,
    selection_func: Callable[[List[Dict[str, Any]]], Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Create a mating pool using the specified selection method.
    
    Args:
        population: List of candidate solutions with fitness scores
        pool_size: Size of the mating pool to create
        selection_func: Function to use for selection
        
    Returns:
        Mating pool of selected candidates
    """
    return [selection_func(population) for _ in range(pool_size)]
