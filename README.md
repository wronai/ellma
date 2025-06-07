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
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📚 Documentation](#-documentation)

## 🚀 Features

ELLMa is a revolutionary **self-evolving AI agent** that runs locally on your machine. Unlike traditional AI tools, ELLMa **learns and improves itself** with these key features:

[![PyPI version](https://badge.fury.io/py/ellma.svg)](https://badge.fury.io/py/ellma)
[![Python Support](https://img.shields.io/pypi/pyversions/ellma.svg)](https://pypi.org/project/ellma/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 What is ELLMa?

ELLMa is a revolutionary **self-evolving AI agent** that runs locally on your machine. Unlike traditional AI tools, ELLMa **learns and improves itself** by:

### Core Capabilities

- 🧬 **Self-Evolution**: Automatically generates new capabilities based on usage patterns
- 🏠 **Local-First**: Runs entirely on your machine with complete privacy
- 🐚 **Shell-Native**: Integrates seamlessly with your system and workflows
- 🛠️ **Command Execution**: Executes commands in a structured format
- 📦 **Modular**: Extensible architecture that grows with your needs
- 🤖 **Multi-Model**: Supports various local LLM models
- 🔄 **Auto-Improving**: Continuously learns from interactions

### Technical Highlights

- **Built-in Commands**: Wide range of system, web, and file operations
- **Code Generation**: Generate Python, Bash, and Docker configurations
- **Web Interaction**: Advanced web scraping and API interaction tools
- **Plugin System**: Easy to extend with custom modules
- **Performance Monitoring**: Built-in metrics and monitoring
- **Cross-Platform**: Works on Linux, macOS, and Windows (WSL2 recommended for Windows)

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

3. **Verify your setup**
   ```bash
   # Check system requirements and configuration
   ellma verify
   ```

4. **Start the interactive shell**
   ```bash
   # Start interactive shell
   ellma shell
   
   # Start shell with verbose output
   # ellma -v shell
   ```

5. **Or execute commands directly**
   ```bash
   # System information
   ellma exec system.scan
   
   # Web interaction (extract text and links)
   ellma exec web.read https://example.com --extract-text --extract-links
   
   # File operations (search for Python files)
   ellma exec files.search /path/to/directory --pattern "*.py"
   
   # Get agent status
   ellma status
   ```

## 🛠 Development

## 🛠 Development

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/wronai/ellma.git
   cd ellma
   ```

2. **Install with development dependencies**
   ```bash
   pip install -e ".[dev]"
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

# Run multiple evolution cycles
ellma evolve --cycles 3

# Force evolution even if no improvements are detected
ellma evolve --force

# Run evolution with specific parameters
ellma evolve --learning-rate 0.2 --max-depth 5
```

### Monitoring Evolution

```bash
# View evolution history
cat ~/.ellma/evolution/evolution_history.json | jq .

# Monitor evolution logs
tail -f ~/.ellma/logs/evolution.log

# Get evolution status
ellma status --evolution
```

### Evolution Configuration

You can configure the evolution process in `~/.ellma/config.yaml`:

```yaml
evolution:
  enabled: true
  auto_improve: true
  learning_rate: 0.1
  max_depth: 3
  max_iterations: 100
  early_stopping: true
```

## 🧩 Extending ELLMa

### Creating Custom Commands

1. Create a new Python module in `ellma/commands/`:

```python
from ellma.commands.base import BaseCommand

class MyCustomCommand(BaseCommand):
    """My custom command"""
    
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

# View performance metrics
ellma exec system.metrics
```

### 🔍 Advanced Command Usage

```bash
# Chain multiple commands
ellma exec "system.scan && web.read https://example.com"

# Save command output to file
ellma exec system.scan scan_results.json

# Use different output formats
ellma exec system.info json
ellma exec system.info yaml
```

### 🐚 Powerful Shell Interface
Natural language commands that translate to system operations:

```bash
ellma> system scan network ports
ellma> generate bash script for backup
ellma> analyze this log file for errors
ellma> create docker setup for web app
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
# Get system overview
ellma exec system.overview

# Monitor system resources
ellma exec system.monitor --cpu --memory --disk

# Find large files
ellma exec files.find_large --path /var --min-size 100M

# Check network connections
ellma exec system.network_connections
```

### Development Workflow

```bash
# Generate a new Python project
ellma generate python --task "FastAPI project with SQLAlchemy and JWT auth"

# Create a Docker Compose setup
ellma generate docker --task "Python app with PostgreSQL and Redis"

# Generate test cases
ellma generate test --file app/main.py --framework pytest

# Document a Python function
ellma exec code.document_function utils.py --function process_data
```

### Web & API Interaction

```bash
# Read and extract content from a webpage
ellma exec web.read https://example.com --extract-text --extract-links

# Test API endpoints
ellma exec web.test_endpoint https://api.example.com/data --method GET

# Generate API client code
ellma generate python --task "API client for REST service with error handling"
```

### Data Processing

```bash
# Analyze CSV data
ellma exec "data.analyze --file data.csv --format csv"

# Convert between data formats
ellma exec "data.convert --input data.json --output data.yaml"

# Generate data visualization
ellma generate python --task "Plot time series data from CSV"
```

### Custom Commands

```bash
# List available commands
ellma exec system.commands

# Get help for a specific command
ellma exec "help system.scan"

# Create a custom command
ellma exec "command.create --name hello --code 'echo \"Hello, World!\"'"
```
ellma generate python --task="Scrape product prices with retry logic"
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
git clone https://github.com/ellma-ai/ellma.git
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
- 🐛 [Issue Tracker](https://github.com/ellma-ai/ellma/issues)
- 💬 [Discussions](https://github.com/ellma-ai/ellma/discussions)
- 📧 [Email Support](mailto:support@ellma.dev)

---

**ELLMa: The AI agent that grows with you** 🌱→🌳