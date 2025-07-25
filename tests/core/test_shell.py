"""
Tests for the ELLMa interactive shell module.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from ellma.core.shell import InteractiveShell, ELLMaCompleter


@pytest.fixture
def mock_agent():
    """Create a mock agent with minimal required attributes."""
    agent = MagicMock()
    agent.home_dir = Path("/tmp/ellma_test")
    agent.commands = {
        "module1": MagicMock(__name__="module1"),
        "module2": MagicMock(__name__="module2"),
    }
    # Add some mock commands to the modules
    agent.commands["module1"].action1 = MagicMock()
    agent.commands["module1"].action2 = MagicMock()
    agent.commands["module2"].do_something = MagicMock()
    
    # Mock the get_status method to return a proper status dictionary
    agent.get_status.return_value = {
        'version': '0.1.6',
        'model_loaded': True,
        'model_path': '/path/to/model',
        'modules_count': 2,
        'commands_count': 3,
        'performance_metrics': {
            'commands_executed': 10,
            'successful_executions': 9,
            'evolution_cycles': 1
        }
    }
    
    return agent


def test_ellma_completer_initialization(mock_agent):
    """Test that the ELLMaCompleter initializes correctly."""
    completer = ELLMaCompleter(mock_agent)
    
    # Should have collected commands from the mock agent
    assert len(completer.commands) > 0
    assert "module1.action1" in completer.commands
    assert "module1.action2" in completer.commands
    assert "module2.do_something" in completer.commands


def test_ellma_completer_get_completions(mock_agent):
    """Test command completion functionality."""
    completer = ELLMaCompleter(mock_agent)
    
    # Mock document and complete_event
    class MockDocument:
        def __init__(self, text):
            self.text = text
        def get_word_before_cursor(self):
            return self.text
    
    # Test completion for partial command
    doc = MockDocument("mod")
    completions = list(completer.get_completions(doc, None))
    assert len(completions) >= 2  # At least module1 and module2
    
    # Test completion for specific module
    doc = MockDocument("module1.")
    completions = list(completer.get_completions(doc, None))
    # Check that we have at least the expected completions
    completion_texts = [c.text for c in completions]
    assert "module1.action1" in completion_texts
    assert "module1.action2" in completion_texts


def test_interactive_shell_initialization(mock_agent, tmp_path):
    """Test that the InteractiveShell initializes correctly."""
    # Set a temporary home directory for testing
    mock_agent.home_dir = tmp_path
    
    shell = InteractiveShell(mock_agent)
    
    assert shell.agent == mock_agent
    assert shell.running is True
    # Check if history file was created (the file is created on first use, not at init)
    # So we'll just check that the path is set correctly
    assert str(shell.history_file) == str(tmp_path / "shell_history.txt")


def test_shell_help_command(mock_agent):
    """Test the help command functionality."""
    shell = InteractiveShell(mock_agent)
    
    # Test the help command directly
    with patch.object(shell.console, 'print') as mock_print:
        result = shell._cmd_help([])
        assert result == "Help displayed"
        mock_print.assert_called()
        
    # Test help for a specific command
    with patch.object(shell.console, 'print') as mock_print:
        result = shell._cmd_help(["status"])
        assert "status" in result
        assert "Show agent status" in result


def test_shell_exit_command(mock_agent):
    """Test that the exit command stops the shell."""
    shell = InteractiveShell(mock_agent)
    
    # Test that _cmd_exit sets running to False
    assert shell.running is True
    result = shell._cmd_exit([])
    assert result == "Goodbye!"
    assert shell.running is False
