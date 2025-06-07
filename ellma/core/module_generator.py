"""
Module generator for ELLMa evolution process.

This module handles the generation of new modules with standardized structure,
including Dockerfile, tests, and Makefile.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import uuid
import logging

from .error_logger import log_error

logger = logging.getLogger(__name__)

class ModuleGenerator:
    """
    Generates new modules with standardized structure during evolution.
    """
    
    def __init__(self, base_path: str = "modules"):
        """
        Initialize the module generator.
        
        Args:
            base_path: Base path where modules will be generated
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def generate_module(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new module based on the specification.
        
        Args:
            spec: Module specification containing:
                - name: Module name (will be converted to snake_case)
                - description: Module description
                - purpose: What problem this module solves
                - dependencies: List of required Python packages
                
        Returns:
            Dict with generation results and metadata
        """
        try:
            module_name = self._sanitize_name(spec['name'])
            module_dir = self.base_path / module_name
            
            if module_dir.exists():
                module_dir = self._get_unique_name(module_dir)
                module_name = module_dir.name
            
            # Create basic structure
            (module_dir / "tests").mkdir(parents=True, exist_ok=True)
            
            # Generate files
            self._generate_readme(module_dir, spec, module_name)
            self._generate_pyproject(module_dir, spec, module_name)
            self._generate_main(module_dir, spec, module_name)
            self._generate_tests(module_dir, spec, module_name)
            self._generate_dockerfile(module_dir, spec, module_name)
            self._generate_makefile(module_dir, spec, module_name)
            
            return {
                "status": "success",
                "module_name": module_name,
                "module_path": str(module_dir),
                "files_created": [
                    str(p.relative_to(module_dir)) 
                    for p in module_dir.rglob('*') 
                    if p.is_file()
                ]
            }
            
        except Exception as e:
            error_msg = f"Failed to generate module: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_error(e, {"context": "module_generation", "spec": spec})
            return {
                "status": "error",
                "error": error_msg,
                "module_name": spec.get('name', 'unknown'),
                "module_path": ""
            }
    
    def _sanitize_name(self, name: str) -> str:
        """Convert a name to a valid Python module name."""
        # Convert to lowercase and replace spaces with underscores
        name = name.lower().replace(' ', '_')
        # Remove any characters that aren't alphanumeric or underscore
        return ''.join(c for c in name if c.isalnum() or c == '_')
    
    def _get_unique_name(self, path: Path) -> Path:
        """Get a unique directory name by appending a number if needed."""
        counter = 1
        new_path = path
        while new_path.exists():
            new_path = path.parent / f"{path.name}_{counter}"
            counter += 1
        return new_path
    
    def _generate_readme(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate README.md for the module."""
        content = f"""# {spec['name']}

{spec.get('description', 'No description provided.')}

## Purpose
{spec.get('purpose', 'No specific purpose defined.')}

## Installation

```bash
# Install in development mode
pip install -e .

# Or install with all dependencies
pip install ".[dev]"
```

## Usage

```python
from {module_name}.main import {spec['name'].title().replace(' ', '')}Module

# Initialize the module
module = {spec['name'].title().replace(' ', '')}Module()

# Use the module
result = module.example_method()
```

## Testing

Run tests with pytest:

```bash
make test
# or
pytest tests/ -v
```

## Building

Build a Docker image:

```bash
make docker-build
```

Run the container:

```bash
make docker-run
```
"""
        (module_dir / "README.md").write_text(content)
    
    def _generate_pyproject(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate pyproject.toml for the module."""
        dependencies = spec.get('dependencies', [])
        
        content = f"""[build-system]
requires = ["setuptools>=42"]
build-backend = "setuptools.build_meta"

[project]
name = "{module_name}"
version = "0.1.0"
description = "{spec.get('description', '')}"
requires-python = ">=3.8"
dependencies = [
    "pytest>=6.0",
    "numpy>=1.20.0",
    {deps}
]

[project.optional-dependencies]
dev = [
    "pytest-cov",
    "black",
    "mypy",
    "flake8"
]
""".format(
            deps='\n    '.join(f'"{dep}",' for dep in dependencies) if dependencies else ''
        )
        
        (module_dir / "pyproject.toml").write_text(content)
    
    def _generate_main(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate the main module file."""
        class_name = spec['name'].title().replace(' ', '')
        module_name_sanitized = self._sanitize_name(spec['name'])
        
        content = f"""\"\"\"
{spec['name']} Module

This module provides functionality for {spec.get('purpose', 'a specific task')}.
\"\"\"

class {class_name}Module:
    \"\"\"
    {spec.get('description', 'Module for performing specific tasks.')}
    \"\"\"
    
    def __init__(self):
        \"\"\"Initialize the module.\"\"\"
        self.name = "{spec['name']}"
        self.version = "0.1.0"
    
    def example_method(self, input_value: str = None) -> dict:
        \"\"\"
        An example method that processes input and returns a result.
        
        Args:
            input_value: Optional input string to process
            
        Returns:
            dict: A dictionary containing the processed result
        """
        if input_value is None:
            input_value = "default"
            
        return {{
            "status": "success",
            "result": f"Processed: {{input_value}}",
            "module": self.name,
            "version": self.version
        }}
    
    def get_commands(self) -> dict:
        """
        Return the commands provided by this module.
        
        Returns:
            dict: Dictionary of command names and their corresponding methods
        """
        return {
            f"{spec['name'].lower().replace(' ', '_')}_command": self.example_method
        }
"""
        
        # Create module directory and __init__.py
        (module_dir / module_name).mkdir(exist_ok=True)
        (module_dir / module_name / "__init__.py").write_text(
            f""""""{spec['name']} module."""

from .main import {class_name}Module

__all__ = ['{class_name}Module']
"""
        )
        
        # Write main module
        (module_dir / module_name / "main.py").write_text(content)
    
    def _generate_tests(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate test files for the module."""
        class_name = spec['name'].title().replace(' ', '')
        command_name = f"{spec['name'].lower().replace(' ', '_')}_command"
        
        test_content = f""""""Tests for the {module_name} module."""
import pytest
from {module_name}.main import {class_name}Module


def test_module_initialization():
    \"\"\"Test that the module initializes correctly.\"\"\"
    module = {class_name}Module()
    assert module.name == \"{spec['name']}\"
    assert module.version == \"0.1.0\"


def test_example_method_default():
    \"\"\"Test the example method with default input.\"\"\"
    module = {class_name}Module()
    result = module.example_method()
    assert result[\"status\"] == \"success\"
    assert \"Processed: default\" in result[\"result\"]


def test_example_method_custom_input():
    \"\"\"Test the example method with custom input.\"\"\"
    module = {class_name}Module()
    test_input = \"test input\"
    result = module.example_method(test_input)
    assert result[\"status\"] == \"success\"
    assert f\"Processed: {{test_input}}\" in result[\"result\"]


def test_get_commands():
    \"\"\"Test that the module returns its commands correctly.\"\"\"
    module = {class_name}Module()
    commands = module.get_commands()
    assert \"{command_name}\" in commands
    assert callable(commands[\"{command_name}\"])


if __name__ == "__main__":
    pytest.main(["-v", __file__])
""".format(
            module_name=module_name,
            class_name=class_name,
            name=spec['name'],
            command_name=spec['name'].lower().replace(' ', '_') + '_command'
        )
        
        (module_dir / "tests").mkdir(exist_ok=True)
        (module_dir / "tests" / f"test_{module_name}.py").write_text(test_content)
        (module_dir / "tests" / "__init__.py").touch()
    
    def _generate_dockerfile(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate a Dockerfile for the module."""
        content = f"""# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:$PYTHONPATH"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir -e .[dev]

# Run tests when the container launches
CMD ["pytest", "tests/", "-v"]
"""
        (module_dir / "Dockerfile").write_text(content)
    
    def _generate_makefile(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate a Makefile for common tasks."""
        content = """# Makefile for {name}

# Variables
PYTHON = python3
PIP = pip3
DOCKER = docker
DOCKER_IMAGE = {image_name}
DOCKER_TAG = latest

.PHONY: install test lint format type-check docker-build docker-run docker-push clean

# Install the package in development mode
install:
	$(PIP) install -e .[dev]

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Lint the code
lint:
	black --check {module_name} tests/
	flake8 {module_name} tests/

# Format the code
format:
	black {module_name} tests/

# Run type checking
type-check:
	mypy {module_name} tests/

# Build Docker image
docker-build:
	$(DOCKER) build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run Docker container
docker-run:
	$(DOCKER) run --rm -it $(DOCKER_IMAGE):$(DOCKER_TAG)

# Push Docker image
docker-push:
	$(DOCKER) push $(DOCKER_IMAGE):$(DOCKER_TAG)

# Clean up
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ __pycache__/ */__pycache__
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
""".format(
            name=spec['name'],
            module_name=module_name,
            image_name=f"ellma-{module_name}"
        )
        
        (module_dir / "Makefile").write_text(content)
