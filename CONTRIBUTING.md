# Contributing to ELLMa

Thank you for your interest in contributing to ELLMa! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/ellma.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install in development mode: `pip install -e .[dev]`
6. Create a feature branch: `git checkout -b feature/your-feature-name`
7. Make your changes
8. Run tests: `pytest`
9. Submit a pull request

## 📋 Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/wronai/ellma.git
cd ellma

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Verify Installation

```bash
# Run basic tests
pytest tests/

# Check code formatting
black --check ellma/
flake8 ellma/

# Run type checking
mypy ellma/

# Test CLI
ellma --help
```

## 🏗️ Architecture Overview

ELLMa follows a modular architecture:

```
ellma/
├── core/           # Core agent functionality
├── commands/       # Command modules
├── generators/     # Code generators
├── modules/        # Dynamic module system
├── utils/          # Utility functions
└── cli/           # Command line interface
```

### Key Components

1. **Agent (core/agent.py)**: Main orchestrator
2. **Evolution Engine (core/evolution.py)**: Self-improvement system
3. **Commands**: Modular command system
4. **Generators**: Code generation engines
5. **Module Registry**: Dynamic module loading

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=ellma

# Run integration tests
pytest tests/integration/
```

### Testing with Optional Dependencies

ELLMa includes optional audio features that require additional dependencies. The test suite is designed to work both with and without these dependencies.

#### Testing Without Audio Dependencies

By default, tests that require audio dependencies will be skipped if the dependencies are not installed:

```bash
# Run tests without audio dependencies
pytest tests/
```

#### Testing With Audio Dependencies

To test with audio features, install the audio extras and set the `TEST_AUDIO` environment variable:

```bash
# Install with audio dependencies
pip install -e .[dev,audio]

# Run tests with audio features
export TEST_AUDIO=1  # On Windows: set TEST_AUDIO=1
pytest tests/
```

### Writing Tests

When writing tests that depend on optional features:

1. Use the `@pytest.mark.audio` decorator for tests that require audio features
2. Check for required dependencies at runtime using `pytest.importorskip`
3. Provide meaningful skip messages when dependencies are missing

Example:

```python
import pytest

def test_audio_feature():
    # Skip if audio dependencies are not available
    pytest.importorskip("pyaudio")
    
    # Test audio functionality
    ...
```

### Writing Tests

- Use pytest for testing framework
- Follow naming convention: `test_*.py`
- Mock external dependencies
- Test both success and failure cases
- Include docstrings explaining test purpose

Example test:

```python
def test_agent_initialization():
    """Test that agent initializes correctly."""
    agent = ELLMa()
    assert agent is not None
    assert hasattr(agent, 'commands')
```

## 📝 Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all functions
- Docstrings for all public functions and classes
- Use f-strings for string formatting

### Code Formatting

```bash
# Format code with Black
black ellma/

# Check with flake8
flake8 ellma/

# Sort imports
isort ellma/
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.0.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 5.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
```

## 📚 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with default value
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: Description of when this exception is raised
        
    Example:
        >>> result = example_function("hello", 42)
        >>> print(result)
        True
    """
    pass
```

### Adding New Commands

To add a new command module:

1. Create file in `ellma/commands/`
2. Inherit from `BaseCommand`
3. Implement required methods
4. Add to `__init__.py`
5. Write tests
6. Update documentation

Example:

```python
from ellma.commands.base import BaseCommand

class NewCommands(BaseCommand):
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "new"
        self.description = "New command functionality"
    
    def action(self, param: str) -> str:
        """Perform new action."""
        return f"Result: {param}"
```

## 🔧 Adding New Generators

To add a new code generator:

1. Create file in `ellma/generators/`
2. Implement `generate()` method
3. Add templates and patterns
4. Include validation
5. Write tests

Example structure:

```python
class NewGenerator:
    def __init__(self, agent):
        self.agent = agent
        self.templates = self._load_templates()
    
    def generate(self, task_description: str, **kwargs) -> str:
        # Generation logic here
        pass
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, ELLMa version)
5. **Error messages** and stack traces
6. **Minimal example** that demonstrates the issue

Use this template:

```markdown
## Bug Description
Brief description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.0]
- ELLMa: [e.g., 0.1.0]

## Additional Context
Any other relevant information.
```

## 💡 Feature Requests

When suggesting new features:

1. **Explain the use case** and motivation
2. **Describe the proposed solution** clearly
3. **Consider alternatives** and their trade-offs
4. **Provide examples** of how it would be used
5. **Discuss implementation** if you have ideas

## 🔀 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Changelog updated (if significant change)
- [ ] Pre-commit hooks pass

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No unnecessary changes included
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainer
3. **Testing** in different environments
4. **Documentation** review
5. **Merge** when approved

## 🏆 Recognition

Contributors will be:

- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation
- Invited to join core team (for significant contributions)

## 📞 Getting Help

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and features
- **Chat**: Join our Discord/Slack (links in README)
- **Email**: Contact maintainers directly for sensitive issues

## 🎯 Areas for Contribution

### High Priority

- [ ] Additional command modules
- [ ] More code generators
- [ ] Performance optimizations
- [ ] Documentation improvements
- [ ] Test coverage increase

### Medium Priority

- [ ] Web interface
- [ ] Mobile support
- [ ] Cloud integrations
- [ ] Additional LLM backends
- [ ] Plugin marketplace

### Low Priority

- [ ] GUI application
- [ ] Desktop notifications
- [ ] Metrics dashboard
- [ ] Advanced analytics
- [ ] Multi-language support

## 📄 License

By contributing to ELLMa, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Every contribution helps make ELLMa better! Whether it's:

- Reporting bugs
- Suggesting features
- Writing code
- Improving documentation
- Sharing feedback

Your involvement is valuable and appreciated! 🎉