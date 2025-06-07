# 🧬 ELLMa - Evolutionary Local LLM Agent

> **E**volutionary **L**ocal **LLM** **A**gent - Self-improving AI assistant that evolves with your needs

[![PyPI version](https://badge.fury.io/py/ellma.svg)](https://badge.fury.io/py/ellma)
[![Python Support](https://img.shields.io/pypi/pyversions/ellma.svg)](https://pypi.org/project/ellma/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 What is ELLMa?

ELLMa is a revolutionary **self-evolving AI agent** that runs locally on your machine. Unlike traditional AI tools, ELLMa **learns and improves itself** by:

- 🧬 **Self-Evolution**: Automatically generates new capabilities based on usage patterns
- 🏠 **Local-First**: Runs entirely on your machine with complete privacy
- 🐚 **Shell-Native**: Integrates seamlessly with your system and workflows  
- 🛠️ **Multi-Language**: Generates code in Python, Bash, Groovy, Docker, and more
- 📦 **Modular**: Extensible architecture that grows with your needs

## ⚡ Quick Start
install
```bash
bash ./scripts/install.sh
```

### Installation
```bash
pip install ellma --upgrade
```
local
```bash
pip install -e .
```

### First Steps
```bash
# Initialize ELLMa
ellma init

# Download Mistral 7B model (optional - will auto-download)
ellma setup --download-model

# Start interactive shell
ellma shell

# Or execute commands directly
ellma exec "system.scan"
ellma exec "web.read https://softrec.com"
```

### Your First Evolution
```bash
# Let ELLMa analyze itself and improve
ellma evolve
```

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
# Monitor system health
ellma exec "system.health"

# Generate monitoring script
ellma generate bash --task="Check disk space and send alerts"

# Analyze log files
ellma exec "files.analyze /var/log/syslog --pattern=error"
```

### Development Tasks
```bash
# Generate project structure
ellma generate python --task="FastAPI project with authentication"

# Create deployment configuration
ellma generate docker --task="Production ready web app with nginx"

# Generate test scripts
ellma generate bash --task="Integration testing for REST API"
```

### Web Automation
```bash
# Read and summarize web content
ellma exec "web.read https://news.ycombinator.com --summarize"

# Generate web scraping code
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