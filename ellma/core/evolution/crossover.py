"""
Crossover Operators

This module implements various crossover strategies for the evolution process.
"""

import random
import ast
from typing import Dict, Any, List, Tuple, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass

# Type variable for generic crossover functions
T = TypeVar('T')

@dataclass
class CrossoverResult(Generic[T]):
    """Result of a crossover operation."""
    offspring1: T
    offspring2: T
    success: bool = True
    message: str = ""


def single_point_crossover(parent1: Dict[str, Any], 
                          parent2: Dict[str, Any], 
                          **kwargs) -> CrossoverResult[Dict[str, Any]]:
    """Perform single-point crossover between two parents.
    
    Args:
        parent1: First parent solution
        parent2: Second parent solution
        
    Returns:
        CrossoverResult containing two offspring
    """
    try:
        # For dictionary-based representations
        if not parent1 or not parent2:
            return CrossoverResult(parent1, parent2, False, "Empty parent(s)")
            
        keys = list(parent1.keys())
        if len(keys) < 2:
            return CrossoverResult(parent1, parent2, False, "Not enough keys for crossover")
            
        # Select a random crossover point
        point = random.randint(1, len(keys) - 1)
        
        # Create offspring
        offspring1 = {}
        offspring2 = {}
        
        for i, key in enumerate(keys):
            if i < point:
                offspring1[key] = parent1[key]
                offspring2[key] = parent2[key]
            else:
                offspring1[key] = parent2[key]
                offspring2[key] = parent1[key]
                
        return CrossoverResult(offspring1, offspring2)
        
    except Exception as e:
        return CrossoverResult(
            parent1, parent2, 
            False, 
            f"Crossover failed: {str(e)}"
        )


def uniform_crossover(parent1: Dict[str, Any], 
                     parent2: Dict[str, Any],
                     crossover_rate: float = 0.5,
                     **kwargs) -> CrossoverResult[Dict[str, Any]]:
    """Perform uniform crossover between two parents.
    
    Args:
        parent1: First parent solution
        parent2: Second parent solution
        crossover_rate: Probability of swapping each gene
        
    Returns:
        CrossoverResult containing two offspring
    """
    try:
        if not parent1 or not parent2:
            return CrossoverResult(parent1, parent2, False, "Empty parent(s)")
            
        offspring1 = {}
        offspring2 = {}
        
        for key in parent1.keys():
            if key not in parent2:
                continue
                
            if random.random() < crossover_rate:
                offspring1[key] = parent2[key]
                offspring2[key] = parent1[key]
            else:
                offspring1[key] = parent1[key]
                offspring2[key] = parent2[key]
                
        return CrossoverResult(offspring1, offspring2)
        
    except Exception as e:
        return CrossoverResult(
            parent1, parent2,
            False,
            f"Uniform crossover failed: {str(e)}"
        )


def subtree_crossover(parent1: Dict[str, Any], 
                     parent2: Dict[str, Any],
                     **kwargs) -> CrossoverResult[Dict[str, Any]]:
    """Perform subtree crossover for tree-based representations.
    
    This is useful for genetic programming where solutions are represented as trees.
    
    Args:
        parent1: First parent solution (must have 'tree' key with AST)
        parent2: Second parent solution (must have 'tree' key with AST)
        
    Returns:
        CrossoverResult containing two offspring with swapped subtrees
    """
    try:
        if 'tree' not in parent1 or 'tree' not in parent2:
            return CrossoverResult(parent1, parent2, False, "Missing 'tree' in parent(s)")
            
        # Make deep copies to avoid modifying originals
        tree1 = ast.parse(ast.unparse(parent1['tree']))
        tree2 = ast.parse(ast.unparse(parent2['tree']))
        
        # Get all nodes in both trees
        nodes1 = list(ast.walk(tree1))
        nodes2 = list(ast.walk(tree2))
        
        if not nodes1 or not nodes2:
            return CrossoverResult(parent1, parent2, False, "Empty tree(s)")
            
        # Select random nodes to swap
        node1 = random.choice(nodes1)
        node2 = random.choice(nodes2)
        
        # Swap the nodes
        for field in node1._fields:
            setattr(node1, field, getattr(node2, field, None))
            
        for field in node2._fields:
            setattr(node2, field, getattr(node1, field, None))
            
        # Create offspring
        offspring1 = parent1.copy()
        offspring2 = parent2.copy()
        offspring1['tree'] = tree1
        offspring2['tree'] = tree2
        
        return CrossoverResult(offspring1, offspring2)
        
    except Exception as e:
        return CrossoverResult(
            parent1, parent2,
            False,
            f"Subtree crossover failed: {str(e)}"
        )


def arithmetic_crossover(parent1: Dict[str, Any],
                        parent2: Dict[str, Any],
                        alpha: float = 0.5,
                        **kwargs) -> CrossoverResult[Dict[str, Any]]:
    """Perform arithmetic crossover for real-valued representations.
    
    Args:
        parent1: First parent solution (numeric values only)
        parent2: Second parent solution (numeric values only)
        alpha: Weight for interpolation between parents
        
    Returns:
        CrossoverResult containing two offspring
    """
    try:
        if not parent1 or not parent2:
            return CrossoverResult(parent1, parent2, False, "Empty parent(s)")
            
        offspring1 = {}
        offspring2 = {}
        
        for key in parent1.keys():
            if key not in parent2:
                continue
                
            if isinstance(parent1[key], (int, float)) and isinstance(parent2[key], (int, float)):
                # Linear combination
                val1 = alpha * parent1[key] + (1 - alpha) * parent2[key]
                val2 = (1 - alpha) * parent1[key] + alpha * parent2[key]
                
                # Maintain type consistency
                if isinstance(parent1[key], int) and isinstance(parent2[key], int):
                    val1 = int(round(val1))
                    val2 = int(round(val2))
                    
                offspring1[key] = val1
                offspring2[key] = val2
            else:
                # For non-numeric values, keep parent values
                offspring1[key] = parent1[key]
                offspring2[key] = parent2[key]
                
        return CrossoverResult(offspring1, offspring2)
        
    except Exception as e:
        return CrossoverResult(
            parent1, parent2,
            False,
            f"Arithmetic crossover failed: {str(e)}"
        )
        

def get_crossover_method(name: str) -> Callable:
    """Get a crossover method by name.
    
    Args:
        name: Name of the crossover method
        
    Returns:
        Crossover function
        
    Raises:
        ValueError: If the method name is unknown
    """
    methods = {
        'single_point': single_point_crossover,
        'uniform': uniform_crossover,
        'subtree': subtree_crossover,
        'arithmetic': arithmetic_crossover
    }
    
    if name not in methods:
        raise ValueError(f"Unknown crossover method: {name}")
        
    return methods[name]
