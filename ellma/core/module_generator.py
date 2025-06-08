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
            
            # Create module directory structure
            module_dir.mkdir(exist_ok=True)
            (module_dir / "tests").mkdir(exist_ok=True)
            
            # Generate standard files
            self._generate_readme(module_dir, spec, module_name)
            self._generate_pyproject(module_dir, spec, module_name)
            self._generate_main(module_dir, spec, module_name)
            self._generate_tests(module_dir, spec, module_name)
            self._generate_dockerfile(module_dir, spec, module_name)
            self._generate_makefile(module_dir, spec, module_name)
            
            return {
                'status': 'success',
                'module_name': module_name,
                'module_path': str(module_dir),
                'files_created': [
                    str(module_dir / 'README.md'),
                    str(module_dir / 'pyproject.toml'),
                    str(module_dir / module_name / '__init__.py'),
                    str(module_dir / 'tests' / '__init__.py'),
                    str(module_dir / 'Dockerfile'),
                    str(module_dir / 'Makefile')
                ]
            }
            
        except Exception as e:
            log_error(e, "Error generating module")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _sanitize_name(self, name: str) -> str:
        """Convert a name to a valid Python module name."""
        # Convert to lowercase and replace spaces with underscores
        name = name.lower().replace(' ', '_')
        # Remove invalid characters
        import re
        name = re.sub(r'[^a-z0-9_]', '', name)
        # Ensure it starts with a letter
        if not name[0].isalpha():
            name = 'm_' + name
        return name
    
    def _get_unique_name(self, path: Path) -> Path:
        """Get a unique directory name by appending a number if needed."""
        if not path.exists():
            return path
            
        base = path
        counter = 1
        while path.exists():
            path = base.parent / f"{base.name}_{counter}"
            counter += 1
        return path
    
    def _generate_readme(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate README.md for the module."""
        content = f"""# {spec['name']}

{spec.get('description', '')}

## Purpose
{spec.get('purpose', '')}

## Installation

```bash
pip install -e .
```

## Usage

```python
from {module_name} import main

# Your code here
```

## Development

Install development dependencies:

```bash
pip install -e '.[dev]'
```

Run tests:

```bash
make test
```
"""
        (module_dir / "README.md").write_text(content)
    
    def _generate_pyproject(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate pyproject.toml for the module."""
        content = f"""[build-system]
requires = ["setuptools>=42"]
build-backend = "setuptools.build_meta"

[project]
name = "{module_name}"
version = "0.1.0"
description = "{spec.get('description', '')}"
authors = [
    {{ name = "Your Name", email = "your.email@example.com" }},
]
dependencies = [
    # Add your dependencies here
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "black>=21.5b2",
    "flake8>=3.9.0",
    "mypy>=0.900",
    "pytest-cov>=2.8.0",
]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
"""
        (module_dir / "pyproject.toml").write_text(content)
    
    def _generate_main(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate the main module file."""
        # Create module directory if it doesn't exist
        module_path = module_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)
        
        # Generate module content
        class_name = spec['name'].title().replace(' ', '')
        content = f'''"""{spec['name']} module."""

class {class_name}:
    """{spec.get('description', 'Module implementation.')}"""
    
    def __init__(self):
        self.name = "{module_name}"
        self.version = "0.1.0"
    
    def example_method(self):
        """Example method that returns a greeting."""
        return f"Hello from {{self.name}}!"


def main():
    """Main entry point for the module."""
    module = {class_name}()
    print(module.example_method())


if __name__ == "__main__":
    main()
'''
        
        # Write __init__.py
        init_file = module_path / "__init__.py"
        init_file.write_text(f'"""{spec["name"]} module."""\n')
        init_file.chmod(0o644)
        
        # Write main.py
        main_file = module_path / "main.py"
        main_file.write_text(content)
        main_file.chmod(0o644)
    
    def _generate_tests(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate test files for the module."""
        # Create tests directory if it doesn't exist
        tests_dir = module_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create __init__.py in tests directory
        (tests_dir / "__init__.py").write_text("""Test package for the module.""")
        
        # Create test file content with proper indentation and string formatting
        test_content = f"""\"\"\"
Test cases for {spec['name']}.
\"\"\"

import unittest
from {module_name} import main

class TestMain(unittest.TestCase):
    \"\"\"
    Test cases for the main module.
    \"\"\"
    
    def test_placeholder(self):
        \"\"\"
        Placeholder test.
        \"\"\"
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
"""
        
        # Write test file
        test_file = tests_dir / f"test_{module_name}.py"
        test_file.write_text(test_content)
        test_file.chmod(0o644)  # Ensure proper permissions
    
    def _generate_dockerfile(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate a Dockerfile for the module."""
        content = """# Use Python 3.8 as base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY pyproject.toml .

# Install the package in development mode with all dependencies
RUN pip install --no-cache-dir -e .[dev]

# Copy the rest of the application
COPY . .

# Run tests by default
CMD ["pytest", "tests/", "-v"]
"""
        (module_dir / "Dockerfile").write_text(content)
    
    def _generate_makefile(self, module_dir: Path, spec: Dict[str, Any], module_name: str) -> None:
        """Generate a Makefile for common tasks."""
        content = f"""# Makefile for {spec['name']}

# Variables
PYTHON = python3
PIP = pip3
DOCKER = docker
DOCKER_IMAGE = ellma-{module_name}
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
"""
        (module_dir / "Makefile").write_text(content)

    def get_commands(self) -> Dict[str, Any]:
        """
        Return the commands provided by this module.
        
        Returns:
            dict: Dictionary of command names and their corresponding methods
        """
        return {
            'generate': self.generate_module,
        }
