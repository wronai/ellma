"""
Tests for the example module.
"""
import pytest
from main import ExampleModule

def test_example_module_initialization():
    """Test that the module initializes correctly."""
    module = ExampleModule()
    assert module.name == "Example Module"
    assert module.version == "0.1.0"

def test_example_method_default():
    """Test the example method with default input."""
    module = ExampleModule()
    result = module.example_method()
    assert result["status"] == "success"
    assert "Processed: default" in result["result"]

def test_example_method_custom_input():
    """Test the example method with custom input."""
    module = ExampleModule()
    test_input = "test input"
    result = module.example_method(test_input)
    assert result["status"] == "success"
    assert f"Processed: {test_input}" in result["result"]

def test_get_commands():
    """Test that the module returns its commands correctly."""
    module = ExampleModule()
    commands = module.get_commands()
    assert "example_command" in commands
    assert callable(commands["example_command"])

if __name__ == "__main__":
    pytest.main(["-v", "test.py"])
