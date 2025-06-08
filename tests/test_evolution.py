"""
Tests for the evolution module.
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from ellma.core.evolution.population import Population
from ellma.core.evolution.config import EvolutionConfig
from ellma.core.evolution.fitness import FitnessFunction

class TestPopulation(unittest.TestCase):
    """Test the Population class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = EvolutionConfig(
            population_size=10,
            genome_length=5,
            mutation_rate=0.1,
            crossover_rate=0.7
        )
        self.population = Population(self.config)
    
    def test_initialization(self):
        """Test population initialization."""
        self.assertEqual(len(self.population.individuals), self.config.population_size)
        self.assertEqual(len(self.population.individuals[0].genome), self.config.genome_length)
    
    def test_evaluate(self):
        """Test population evaluation."""
        fitness_func = MagicMock(return_value=1.0)
        self.population.evaluate(fitness_func)
        
        for ind in self.population.individuals:
            self.assertEqual(ind.fitness, 1.0)
        
        self.assertEqual(fitness_func.call_count, self.config.population_size)

class TestFitnessFunction(unittest.TestCase):
    """Test the FitnessFunction class."""
    
    def test_evaluate(self):
        """Test fitness evaluation."""
        fitness_func = FitnessFunction()
        individual = MagicMock()
        individual.genome = np.array([1, 1, 1, 1, 1])
        
        # Simple fitness function that counts ones
        def count_ones(genome):
            return np.sum(genome)
        
        fitness = fitness_func.evaluate(individual, count_ones)
        self.assertEqual(fitness, 5)

class TestEvolutionConfig(unittest.TestCase):
    """Test the EvolutionConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EvolutionConfig()
        self.assertEqual(config.population_size, 50)
        self.assertEqual(config.genome_length, 10)
        self.assertEqual(config.mutation_rate, 0.1)
        self.assertEqual(config.crossover_rate, 0.7)
        self.assertEqual(config.elitism, 1)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = EvolutionConfig(
            population_size=100,
            genome_length=20,
            mutation_rate=0.2,
            crossover_rate=0.8,
            elitism=2
        )
        self.assertEqual(config.population_size, 100)
        self.assertEqual(config.genome_length, 20)
        self.assertEqual(config.mutation_rate, 0.2)
        self.assertEqual(config.crossover_rate, 0.8)
        self.assertEqual(config.elitism, 2)

if __name__ == '__main__':
    unittest.main()
