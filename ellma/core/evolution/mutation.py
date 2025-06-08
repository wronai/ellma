"""
Mutation Operators

This module implements various mutation strategies for the evolution process.
"""

import random
import ast
import inspect
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Callable, TypeVar, Union, Type, Generic
from dataclasses import dataclass

# Type variable for generic mutation functions
T = TypeVar('T')

@dataclass
class MutationResult(Generic[T]):
    """Result of a mutation operation."""
    individual: T
    success: bool = True
    message: str = ""


def gaussian_mutation(individual: Dict[str, Any], 
                      mutation_rate: float = 0.1,
                      scale: float = 0.1,
                      **kwargs) -> MutationResult[Dict[str, Any]]:
    """Apply Gaussian mutation to numeric values in the individual.
    
    Args:
        individual: The individual to mutate
        mutation_rate: Probability of mutating each gene
        scale: Standard deviation of the Gaussian noise
        
    Returns:
        MutationResult containing the mutated individual
    """
    try:
        if not individual:
            return MutationResult(individual, False, "Empty individual")
            
        mutated = individual.copy()
        
        for key, value in mutated.items():
            if not isinstance(value, (int, float)):
                continue
                
            if random.random() < mutation_rate:
                # Apply Gaussian noise
                noise = np.random.normal(0, scale)
                mutated[key] = value + noise
                
                # Maintain type consistency
                if isinstance(value, int):
                    mutated[key] = int(round(mutated[key]))
                    
        return MutationResult(mutated)
        
    except Exception as e:
        return MutationResult(
            individual,
            False,
            f"Gaussian mutation failed: {str(e)}"
        )


def bit_flip_mutation(individual: Dict[str, Any],
                      mutation_rate: float = 0.1,
                      **kwargs) -> MutationResult[Dict[str, Any]]:
    """Apply bit-flip mutation to binary or boolean values.
    
    Args:
        individual: The individual to mutate
        mutation_rate: Probability of flipping each bit/boolean
        
    Returns:
        MutationResult containing the mutated individual
    """
    try:
        if not individual:
            return MutationResult(individual, False, "Empty individual")
            
        mutated = individual.copy()
        
        for key, value in mutated.items():
            if not isinstance(value, (bool, int)):
                continue
                
            if random.random() < mutation_rate:
                if isinstance(value, bool):
                    mutated[key] = not value
                elif isinstance(value, int):
                    # Flip a random bit
                    bit_to_flip = 1 << random.randint(0, value.bit_length())
                    mutated[key] ^= bit_to_flip
                    
        return MutationResult(mutated)
        
    except Exception as e:
        return MutationResult(
            individual,
            False,
            f"Bit-flip mutation failed: {str(e)}"
        )


def subtree_mutation(individual: Dict[str, Any],
                    mutation_rate: float = 0.1,
                    max_depth: int = 5,
                    **kwargs) -> MutationResult[Dict[str, Any]]:
    """Apply subtree mutation for tree-based representations.
    
    Args:
        individual: The individual to mutate (must have 'tree' key with AST)
        mutation_rate: Probability of mutating the individual
        max_depth: Maximum depth of the generated subtree
        
    Returns:
        MutationResult containing the mutated individual
    """
    try:
        if 'tree' not in individual:
            return MutationResult(individual, False, "Missing 'tree' in individual")
            
        if random.random() >= mutation_rate:
            return MutationResult(individual)
            
        # Make a deep copy of the tree
        tree = ast.parse(ast.unparse(individual['tree']))
        
        # Get all nodes in the tree
        nodes = list(ast.walk(tree))
        if not nodes:
            return MutationResult(individual, False, "Empty tree")
            
        # Select a random node to replace
        node_to_replace = random.choice(nodes)
        
        # Generate a new random subtree
        # This is a simplified example - in practice, you'd want more sophisticated generation
        new_node = ast.Num(n=random.randint(0, 100))  # Simple constant as an example
        
        # Replace the node (simplified - in practice, need to handle different node types)
        for field in node_to_replace._fields:
            if field in ['value', 'targets', 'test']:  # Common field names to replace
                setattr(node_to_replace, field, new_node)
                break
                
        # Create mutated individual
        mutated = individual.copy()
        mutated['tree'] = tree
        
        return MutationResult(mutated)
        
    except Exception as e:
        return MutationResult(
            individual,
            False,
            f"Subtree mutation failed: {str(e)}"
        )


def swap_mutation(individual: Dict[str, Any],
                 mutation_rate: float = 0.1,
                 **kwargs) -> MutationResult[Dict[str, Any]]:
    """Apply swap mutation by swapping two values in the individual.
    
    Args:
        individual: The individual to mutate
        mutation_rate: Probability of performing the swap
        
    Returns:
        MutationResult containing the mutated individual
    """
    try:
        if not individual or len(individual) < 2:
            return MutationResult(individual, False, "Not enough elements to swap")
            
        if random.random() >= mutation_rate:
            return MutationResult(individual)
            
        # Select two distinct keys to swap
        keys = list(individual.keys())
        if len(keys) < 2:
            return MutationResult(individual, False, "Not enough keys to swap")
            
        key1, key2 = random.sample(keys, 2)
        
        # Swap the values
        mutated = individual.copy()
        mutated[key1], mutated[key2] = mutated[key2], mutated[key1]
        
        return MutationResult(mutated)
        
    except Exception as e:
        return MutationResult(
            individual,
            False,
            f"Swap mutation failed: {str(e)}"
        )


def get_mutation_method(name: str) -> Callable:
    """Get a mutation method by name.
    
    Args:
        name: Name of the mutation method
        
    Returns:
        Mutation function
        
    Raises:
        ValueError: If the method name is unknown
    """
    methods = {
        'gaussian': gaussian_mutation,
        'bit_flip': bit_flip_mutation,
        'subtree': subtree_mutation,
        'swap': swap_mutation
    }
    
    if name not in methods:
        raise ValueError(f"Unknown mutation method: {name}")
        
    return methods[name]
