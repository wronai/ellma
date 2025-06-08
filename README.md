# 🧬 ELLMa - Evolutionary Local LLM Agent

> **E**volutionary **L**ocal **LLM** **A**gent - Self-improving AI assistant that evolves with your needs

[![PyPI version](https://badge.fury.io/py/ellma.svg)](https://badge.fury.io/py/ellma)
[![Python Support](https://img.shields.io/pypi/pyversions/ellma.svg)](https://pypi.org/project/ellma/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/ellma/badge/?version=latest)](https://ellma.readthedocs.io/)

## 📋 Table of Contents

- [🚀 Features](#-features)
- [⚡ Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [First Steps](#first-steps)
- [🛠 Development](#-development)
- [🔍 Usage Examples](#-usage-examples)
- [🧩 Extending ELLMa](#-extending-ellma)
- [⚙️ Generated Utilities](#️-generated-utilities)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📚 Documentation](#-documentation)

## 🚀 Features

ELLMa is a revolutionary **self-evolving AI agent** that runs locally on your machine. Unlike traditional AI tools, ELLMa **learns and improves itself** with these key features:

### 🔄 Self-Improvement & Evolution

- **Automatic Code Generation**: Generates new modules and capabilities on-the-fly
- **Continuous Learning**: Improves from interactions and feedback
- **Evolution Engine**: Self-modifying architecture that evolves over time
- **Performance Optimization**: Identifies and implements performance improvements
- **Error Recovery**: Automatically detects and recovers from errors

### 🔒 Security & Dependency Management

- **Automatic Environment Setup**: Ensures all dependencies are installed and configured correctly
- **Dependency Auto-Repair**: Automatically detects and fixes missing or broken dependencies
- **Virtual Environment Management**: Handles Python virtual environments automatically
- **Security Checks**: Performs security validations before executing commands
- **Graceful Degradation**: Works even when optional dependencies are missing

### 🎙️ Audio Features (Optional)

ELLMa includes optional audio capabilities that can be enabled by installing the audio extras. These features require additional system dependencies.

#### Audio Features

- **Speech Recognition**: Convert speech to text
- **Text-to-Speech**: Convert text to speech (coming soon)

#### Installation

To install with audio support:

```bash
pip install ellma[audio]
```

#### System Dependencies

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev
```

**On Fedora/RHEL:**
```bash
sudo dnf install -y python3-devel alsa-lib-devel portaudio-devel
```

**On macOS (using Homebrew):**
```bash
brew install portaudio
```

**Note:** Audio features are optional. If you don't need them, you can use ELLMa without installing these dependencies.
- **Audio Processing**: Work with audio files and streams

To install with audio support:
```bash
poetry install --extras "audio"
# or with pip
pip install ellma[audio]
```

Note: Audio features require system dependencies. On Fedora/RHEL:
```bash
sudo dnf install python3-devel alsa-lib-devel portaudio-devel
```

On Ubuntu/Debian:
```bash
sudo apt-get install python3-dev portaudio19-dev
```

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip
- System dependencies (for audio features, see above)

### 🛠 Commands

```bash
# Check environment status
ellma security check

# Install dependencies
ellma security install [--group GROUP]

# Repair environment issues
ellma security repair
```

[![PyPI version](https://badge.fury.io/py/ellma.svg)](https://badge.fury.io/py/ellma)
[![Python Support](https://img.shields.io/pypi/pyversions/ellma.svg)](https://pypi.org/project/ellma/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 What is ELLMa?

ELLMa is a revolutionary **self-evolving AI agent** that runs locally on your machine. Unlike traditional AI tools, ELLMa **learns and improves itself** by:

### Core Capabilities

- **Performance Monitoring**: Built-in metrics and monitoring
- **Cross-Platform**: Works on Linux, macOS, and Windows (WSL2 recommended for Windows)
- **System Introspection**: Built-in commands for system exploration and debugging

### System Introspection

ELLMa includes powerful introspection capabilities to help you understand and debug the system:

```python
# View configuration
sys config                # Show all configuration
sys config model         # Show model configuration

# Explore source code
sys source ellma.core.agent.ELLMa  # View class source
sys code ellma.commands.system     # View module source

# System information
sys info                 # Show detailed system info
sys status               # Show system status
sys health              # Run system health check

# Module exploration
sys modules             # List all available modules
sys module ellma.core   # Show info about a module

# Command help
sys commands           # List all available commands
sys help               # Show help for system commands
```

These commands support natural language queries, so you can type things like:
- "show me the config" → `sys config`
- "what modules are available" → `sys modules`
- "display system information" → `sys info`

## 🛡️ Security and Dependency Management

ELLMa includes a comprehensive security and dependency management system that ensures safe and reliable execution:

### 🔒 Security Features

- **Secure Code Execution**: All code runs in a sandboxed environment with restricted permissions
- **Dependency Validation**: Automatic verification of required packages and versions
- **Environment Isolation**: Each component runs in its own isolated environment
- **Audit Logging**: Detailed logging of all security-relevant actions
- **Automatic Repair**: Self-healing capabilities for common issues
- **Secure Defaults**: Secure by default with sensible restrictions

### 📦 Dependency Management

- **Automatic Dependency Resolution**: Automatically installs missing dependencies
- **Version Conflict Resolution**: Handles version conflicts gracefully
- **Dependency Isolation**: Each module can specify its own dependencies
- **Security Scanning**: Regular security scans for known vulnerabilities

### 🛠️ Using the Secure Executor

Run any Python script or module securely:

```bash
# Run a script with dependency checking
ellma-secure path/to/script.py

# Interactive secure Python shell
ellma-secure

# Install dependencies from requirements.txt
ellma-secure --requirements requirements.txt
```

### 🛡️ Security Context Manager

Use the security context manager in your code:

```python
from ellma.core.security import SecurityContext, Dependency

# Define dependencies
dependencies = [
    Dependency(name="numpy", min_version="1.20.0"),
    Dependency(name="pandas", min_version="1.3.0")
]

# Run code in a secure context
with SecurityContext(dependencies):
    import numpy as np
    import pandas as pd
    # Your secure code here
```

### 🔄 Automatic Dependency Checking

Add dependency checking to any function:

```python
from ellma.core.decorators import secure
from ellma.core.security import Dependency

@secure(dependencies=[
    Dependency(name="requests", min_version="2.25.0"),
    Dependency(name="numpy", min_version="1.20.0")
])
def process_data(url: str) -> dict:
    import requests
    import numpy as np
    # Your function code here
```

### 🚀 Setup and Configuration

1. **Install development dependencies**:
   ```bash
   poetry install --with dev
   ```

2. **Run security checks**:
   ```bash
   # Run bandit security scanner
   bandit -r ellma/
   
   # Check for vulnerable dependencies
   safety check
   ```

3. **Update dependencies**:
   ```bash
   # Update all dependencies
   poetry update
   
   # Update a specific package
   poetry update package-name
   ```

## ⚡ Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (for development)
- 8GB+ RAM recommended for local models
- For GPU acceleration: CUDA-compatible GPU (optional)

### Installation

#### Option 1: Install from source (recommended for development)
```bash
# Clone the repository
git clone https://github.com/wronai/ellma.git
cd ellma

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

#### Option 2: Install via pip
```bash
pip install ellma
```

### First Steps

1. **Initialize ELLMa** (creates config in ~/.ellma)
   ```bash
   # Basic initialization
   ellma init
   
   # Force re-initialization
   # ellma init --force
   ```

2. **Download a model** (or let it auto-download when needed)
   ```bash
   # Download default model
   ellma download-model
   
   # Specify a different model
   # ellma download-model --model mistral-7b-instruct
   ```

3. **Start the interactive shell**
   ```bash
   # Start interactive shell
   ellma shell
   
   # Start shell with verbose output
   # ellma -v shell
   ```

5. **Or execute commands directly**
   ```bash
   # System information
   ellma exec system scan
   
   # Web interaction (extract text and links)
   ellma exec web read https://example.com --extract-text --extract-links
   
   # File operations (search for Python files)
   ellma exec files search /path/to/directory --pattern "*.py"
   
   # Get agent status
   ellma status
   ```

## 🛠 Development

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/wronai/ellma.git
   cd ellma
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   pip install pytest pytest-cov pytest-mock
   ```

4. **Install runtime dependencies**
   ```bash
   pip install SpeechRecognition pyttsx3
   ```

### Running Tests

Run all tests:
```bash
pytest -v
```

Run tests with coverage report:
```bash
pytest --cov=ellma --cov-report=term-missing
```

### Evolution Engine

The evolution engine is a core component that enables self-improvement. It works by:
1. Analyzing system performance and capabilities
2. Identifying improvement opportunities
3. Generating and testing new code
4. Integrating successful changes

To manually trigger an evolution cycle:
```python
from ellma.core.agent import ELLMa

agent = ELLMa()
agent.evolve()
```

### Code Style

We use `black` for code formatting and `flake8` for linting. Before submitting a PR, please run:

```bash
black .
flake8
```

3. **Set up pre-commit hooks** (recommended)
   ```bash
   pre-commit install
   ```

### Development Workflow

#### Running Tests
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_web_commands.py -v

# Run with coverage report
make test-coverage
```

#### Code Quality
```bash
# Run linters
make lint

# Auto-format code
make format

# Type checking
make typecheck

# Security checks
make security
```

#### Documentation
```bash
# Build documentation
make docs

# Serve docs locally
cd docs && python -m http.server 8000
```

### Project Structure

```
ellma/
├── ellma/                  # Main package
│   ├── core/              # Core functionality
│   ├── commands/          # Built-in commands
│   ├── generators/        # Code generation
│   ├── models/           # Model management
│   └── utils/            # Utilities
├── tests/                 # Test suite
├── docs/                 # Documentation
└── scripts/              # Development scripts
```

### Project Structure

```
ellma/
├── ellma/                  # Main package
│   ├── core/              # Core functionality
│   ├── commands/          # Built-in commands
│   ├── generators/        # Code generation
│   ├── models/           # Model management
│   └── utils/            # Utilities
├── tests/                 # Test suite
├── docs/                 # Documentation
└── scripts/              # Development scripts
```

## 🔄 Evolution & Self-Improvement

ELLMa's evolution engine allows it to analyze its performance and automatically improve its capabilities.

### Running Evolution

```bash
# Run a single evolution cycle
ellma evolve

# Run multiple evolution cycles (up to 3 recommended)
ellma evolve --cycles 3

# Force evolution even if not enough commands have been executed
ellma evolve --force
```

### Evolution Requirements
- At least 10 commands should be executed before evolution is recommended
- Use `--force` to bypass this requirement
- Evolution status is shown in the main status output

### Monitoring Evolution

```bash
# View evolution history (if available)
cat ~/.ellma/evolution/evolution_history.json | jq .

# Monitor evolution logs
tail -f ~/.ellma/logs/evolution.log

# Check evolution status in the main status output
ellma status
```

### 🧬 Evolution Configuration

Customize the self-improvement process in `~/.ellma/config.yaml`:

```yaml
evolution:
  enabled: true               # Enable/disable evolution
  auto_improve: true         # Allow automatic improvements
  learning_rate: 0.1         # Learning rate for evolution (0.0-1.0)
```

### Status Information

The main status command shows key evolution metrics:
```bash
ellma status
```

Example output:
```
🤖 ELLMa Status                        
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property               ┃ Value                                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Version                │ 0.1.6                                   │
│ Model Loaded           │ ✅ Yes                                  │
│ Model Path             │ /path/to/model.gguf                     │
│ Modules                │ 0                                       │
│ Commands               │ 3                                       │
│ Commands Executed      │ 15                                      │
│ Success Rate           │ 100.0%                                  │
│ Evolution Cycles       │ 0                                       │
│ Modules Created        │ 0                                       │
└────────────────────────┴─────────────────────────────────────────┘
```
```

### Monitoring Evolution

Track evolution progress and results:

```bash
# View evolution history with detailed metrics
ellma evolution history --limit 10

# Monitor evolution in real-time
ellma evolution monitor

# Get evolution statistics
ellma evolution stats

# Compare evolution cycles
ellma evolution compare cycle1 cycle2
```

### Evolution Best Practices

1. **Start Conservative**: Begin with lower learning rates and enable auto-improve
2. **Monitor Progress**: Regularly check evolution logs and metrics
3. **Set Resource Limits**: Prevent excessive resource usage
4. **Use Benchmarks**: Enable benchmarking to measure improvements
5. **Review Changes**: Periodically review and test evolved modules

### Troubleshooting Evolution

Common issues and solutions:

```bash
# If evolution gets stuck
ellma evolution cancel

# Reset to last known good state
ellma evolution rollback

# Clear evolution cache
ellma evolution clean

# Force reset evolution state (use with caution)
ellma evolution reset --confirm
```

## 🧩 Extending ELLMa

### Creating Custom Commands

1. Create a new Python module in `ellma/commands/`:

```python
from ellma.commands.base import BaseCommand

class MyCustomCommand(BaseCommand):
    """My custom command"""
```

2. Register your command in `ellma/commands/__init__.py`
3. Restart ELLMa to load your new command

## ⚙️ Generated Utilities

ELLMa includes a powerful set of self-generated utilities for common programming tasks. These include:

- 🛡️ **Enhanced Error Handling**: Automatic retries with exponential backoff
- ⚡ **Performance Caching**: In-memory cache with TTL support
- 🚀 **Parallel Processing**: Easy parallel execution of tasks

See the [Generated Utilities Documentation](docs/generated_utilities.md) for detailed usage and examples.
    
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "custom"
        self.description = "My custom command"
    
    def my_action(self, param1: str, param2: int = 42):
        """Example action"""
        return {"result": f"Got {param1} and {param2}"}
```

2. Register your command in `ellma/commands/__init__.py`

### Creating Custom Modules

1. Create a new module class:

```python
from ellma.core.module import BaseModule

class MyCustomModule(BaseModule):
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "my_module"
        self.version = "1.0.0"
    
    def setup(self):
        # Initialization code
        pass
    
    def execute(self, command: str, *args, **kwargs):
        # Handle commands
        if command == "greet":
            return f"Hello, {kwargs.get('name', 'World')}!"
        raise ValueError(f"Unknown command: {command}")
```

2. Register your module in the agent's configuration

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: Open an issue with detailed steps to reproduce
2. **Suggest Features**: Share your ideas for new features
3. **Submit Pull Requests**: Follow these steps:
   - Fork the repository
   - Create a feature branch
   - Make your changes
   - Add tests
   - Update documentation
   - Submit a PR

### Development Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Write docstrings for all public functions and classes
- Add type hints for better code clarity
- Write tests for new features
- Update documentation when making changes

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📚 Documentation

For complete documentation, visit [ellma.readthedocs.io](https://ellma.readthedocs.io/)

## 🙏 Acknowledgments

- Thanks to all contributors who have helped improve ELLMa
- Built with ❤️ by the ELLMa team

## 🎯 Core Features

### 🧬 Self-Evolution Engine

ELLMa continuously improves by analyzing its performance and automatically generating new modules:

```bash
$ ellma evolve
🧬 Starting evolution process...
📊 Analyzing current capabilities...
🎯 Identified 3 improvement opportunities:
   ✅ Added: advanced_file_analyzer
   ✅ Added: network_monitoring
   ✅ Added: code_optimizer
🎉 Evolution complete! 3 new capabilities added.
```

### 📊 Performance Monitoring

Track your agent's performance:
```bash
# Show agent status
ellma status

# View system health metrics
ellma exec system.health
```

### 🔍 Advanced Command Usage

```bash
# Run system scan
ellma exec system.scan

# Read web page content
ellma exec web.read https://example.com

# Read web page with link extraction
ellma exec web.read https://example.com extract_links true extract_text true

# Quick system health check
ellma exec system.health

# Save command output to file
ellma exec system.scan > scan_results.json
```

### 🐚 Interactive Shell Interface

Start the interactive shell and use system commands:

```bash
# Start the interactive shell
ellma shell

# In the shell, you can run commands like:
ellma> system.health
ellma> system.scan
ellma> web.read https://example.com
ellma> web.read https://example.com extract_links true extract_text true
```

Example shell session:
```
🤖 ELLMa Interactive Shell (v0.1.6)
Type 'help' for available commands, 'exit' to quit

# Available commands:
# - system.health: Check system health
# - system.scan: Perform system scan
# - web.read [url]: Read web page content
# - web.read [url] extract_links true extract_text true: Read web page with link extraction
# - help: Show available commands

ellma> system.health
{'status': 'HEALTHY', 'cpu_usage': 12.5, 'memory_usage': 45.2, ...}

ellma> web.read example.com
{'status': 200, 'title': 'Example Domain', 'content_length': 1256, ...}

# For commands with parameters, use space-separated values
ellma> web.read example.com extract_links true extract_text true
```

### 🛠️ Multi-Language Code Generation
Generate production-ready code in multiple languages:

```bash
# Generate Bash scripts
ellma generate bash --task="Monitor system resources and alert on high usage"

# Generate Python code  
ellma generate python --task="Web scraper with rate limiting"

# Generate Docker configurations
ellma generate docker --task="Multi-service web application"

# Generate Groovy for Jenkins
ellma generate groovy --task="CI/CD pipeline with testing stages"
```

### 📊 Intelligent System Integration
ELLMa understands your system and can:

- Scan and analyze system configurations
- Monitor processes and resources
- Automate repetitive tasks
- Generate custom tools for your workflow

## 🏗️ Architecture

```
ellma/
├── core/                   # Core agent and evolution engine
│   ├── agent.py           # Main LLM Agent class
│   ├── evolution.py       # Self-improvement system
│   └── shell.py           # Interactive shell interface
├── commands/               # Modular command system
│   ├── system.py          # System operations
│   ├── web.py             # Web interactions
│   └── files.py           # File operations
├── generators/             # Code generation engines
│   ├── bash.py            # Bash script generator
│   ├── python.py          # Python code generator
│   └── docker.py          # Docker configuration generator
├── modules/                # Dynamic module system
│   ├── registry.py        # Module registry and loader
│   └── [auto-generated]/  # Self-created modules
└── cli/                   # Command-line interface
    ├── main.py            # Main CLI entry point
    └── shell.py           # Interactive shell
```

## 📚 Usage Examples

### System Administration
```bash
# Run comprehensive system scan
ellma exec system.scan

# Monitor system resources (60 seconds with 5-second intervals)
ellma exec system.monitor --duration 60 --interval 5

# Check system health status
ellma exec system.health

# List top processes by CPU usage
ellma exec system.processes --sort-by cpu --limit 10

# Check open network ports
ellma exec system.ports
```

### Development Workflow

```bash
# Generate a new Python project
ellma generate python --task "FastAPI project with SQLAlchemy and JWT auth"

# Create a Docker Compose setup
ellma generate docker --task "Python app with PostgreSQL and Redis"

# Generate test cases
```bash
ellma generate test --file app/main.py --framework pytest

# Document a Python function
ellma exec code document_function utils.py --function process_data
```

### Generated Utilities Examples

Explore practical examples of using the generated utilities in the `examples/generated_utils/` directory:

1. [Error Handling](examples/generated_utils/error_handling_example.py) - Automatic retries with exponential backoff
2. [Performance Caching](examples/generated_utils/cache_example.py) - Efficient data caching with TTL
3. [Parallel Processing](examples/generated_utils/parallel_processing_example.py) - Concurrent task execution
4. [Combined Example](examples/generated_utils/combined_example.py) - Using all utilities together

Run any example with:
```bash
# From the project root
python -m examples.generated_utils.example_name

# Or directly
cd examples/generated_utils/
python example_name.py
```

For more details, see the [generated utilities documentation](docs/generated_utilities.md).


### Web & API Interaction

```bash
# Read and extract content from a webpage
ellma exec web.read https://example.com --extract-text --extract-links

# Make HTTP GET request to an API endpoint
ellma exec web.get https://api.example.com/data

# Make HTTP POST request with JSON data
ellma exec web.post https://api.example.com/data --data '{"key": "value"}'

# Generate API client code
ellma generate python --task "API client for REST service with error handling"
```


```

## 🔧 Configuration

ELLMa stores its configuration in `~/.ellma/`:

```yaml
# ~/.ellma/config.yaml
model:
  path: ~/.ellma/models/mistral-7b.gguf
  context_length: 4096
  temperature: 0.7

evolution:
  enabled: true
  auto_improve: true
  learning_rate: 0.1

modules:
  auto_load: true
  custom_path: ~/.ellma/modules
```

## 🧬 How Evolution Works

1. **Performance Analysis**: ELLMa monitors execution times, success rates, and user feedback
2. **Gap Identification**: Identifies missing functionality or optimization opportunities  
3. **Code Generation**: Uses its LLM to generate new modules and improvements
4. **Testing & Integration**: Automatically tests and integrates new capabilities
5. **Continuous Learning**: Learns from each interaction to become more useful

## 🚀 Advanced Features

### Custom Module Development
```python
# Create custom modules that ELLMa can use and improve
from ellma.core.module import BaseModule

class MyCustomModule(BaseModule):
    def execute(self, *args, **kwargs):
        # Your custom functionality
        return result
```

### API Integration
```python
from ellma import ELLMa

# Use ELLMa programmatically
agent = ELLMa()
result = agent.execute("system.scan")
code = agent.generate("python", task="Data analysis script")
```

### Web Interface (Optional)
```bash
# Install web dependencies
pip install ellma[web]

# Start web interface
ellma web --port 8000
```

## 🛣️ Roadmap

### Version 0.1.6 - MVP ✅
- [x] Core agent with Mistral 7B
- [x] Basic command system
- [x] Shell interface
- [x] Evolution foundation

### Version 0.2.0 - Enhanced Shell
- [ ] Advanced command completion
- [ ] Command history and favorites
- [ ] Real-time performance monitoring
- [ ] Module hot-reloading

### Version 0.3.0 - Code Generation
- [ ] Multi-language code generators
- [ ] Template system
- [ ] Code quality analysis
- [ ] Integration testing

### Version 0.4.0 - Advanced Evolution
- [ ] Performance-based learning
- [ ] User feedback integration
- [ ] Predictive capability development
- [ ] Module marketplace

### Version 1.0.0 - Autonomous Agent
- [ ] Full self-management
- [ ] Advanced reasoning capabilities
- [ ] Multi-agent coordination
- [ ] Enterprise features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/wronai/ellma.git
cd ellma

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run linting
black ellma/
flake8 ellma/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- Inspired by the vision of autonomous AI agents
- Powered by the amazing Mistral 7B model

## 📞 Support

- 📖 [Documentation](https://ellma.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/wronai/ellma/issues)
- 💬 [Discussions](https://github.com/wronai/ellma/discussions)
- 📧 [Email Support](mailto:support@ellma.dev)

---

**ELLMa: The AI agent that grows with you** 🌱→🌳