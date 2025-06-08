"""
Tests for the core functionality of ELLMa.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from ellma.core.agent import Agent
from ellma.core.modular import Module
from ellma.core.shell import InteractiveShell

class TestAgent(unittest.TestCase):
    """Test the Agent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = Agent(name="TestAgent")
    
    def test_agent_initialization(self):
        """Test that an agent initializes correctly."""
        self.assertEqual(self.agent.name, "TestAgent")
        self.assertEqual(len(self.agent.modules), 0)
    
    @patch('ellma.core.agent.Module')
    def test_load_module(self, mock_module):
        """Test loading a module."""
        mock_module_instance = MagicMock()
        mock_module.return_value = mock_module_instance
        
        self.agent.load_module("test_module", "test_module_path")
        
        mock_module.assert_called_once_with("test_module", "test_module_path")
        self.assertIn("test_module", self.agent.modules)
        mock_module_instance.initialize.assert_called_once()

class TestModule(unittest.TestCase):
    """Test the Module class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.module = Module("test_module", "test_module_path")
    
    def test_module_initialization(self):
        """Test that a module initializes correctly."""
        self.assertEqual(self.module.name, "test_module")
        self.assertEqual(self.module.path, "test_module_path")
        self.assertFalse(self.module.initialized)
    
    def test_initialize(self):
        """Test module initialization."""
        self.module.initialize()
        self.assertTrue(self.module.initialized)

class TestInteractiveShell(unittest.TestCase):
    """Test the InteractiveShell class."""
    
    @patch('builtins.print')
    def test_help_command(self, mock_print):
        """Test the help command."""
        shell = InteractiveShell()
        shell.do_help("")
        
        # Check that help text was printed
        self.assertTrue(mock_print.called)
        args, _ = mock_print.call_args
        self.assertIn("Available commands:", args[0])

if __name__ == '__main__':
    unittest.main()
