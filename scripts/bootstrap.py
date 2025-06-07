#!/usr/bin/env python3
"""
ELLMa Bootstrap Script

This script initializes a new ELLMa agent instance with optimal configuration
for the current system and user requirements.
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add current directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ellma import ELLMa, __version__
    from ellma.utils.config import ConfigManager
    from ellma.utils.logger import setup_logging, get_logger
    from ellma.utils.helpers import get_system_info, ensure_directory
except ImportError as e:
    print(f"Error importing ELLMa: {e}")
    print("Please install ELLMa first: pip install ellma")
    sys.exit(1)

# Setup logging
setup_logging(level='INFO', console=True)
logger = get_logger(__name__)


class ELLMaBootstrap:
    """
    ELLMa Bootstrap Manager

    Handles initial setup, configuration optimization, and first-time
    user experience for ELLMa agent.
    """

    def __init__(self):
        self.home_dir = Path.home() / ".ellma"
        self.config_file = self.home_dir / "config.yaml"
        self.models_dir = self.home_dir / "models"
        self.modules_dir = self.home_dir / "modules"
        self.logs_dir = self.home_dir / "logs"

        # System information
        self.system_info = get_system_info()

        # Bootstrap configuration
        self.bootstrap_config = {
            'created_at': datetime.now().isoformat(),
            'system': self.system_info,
            'bootstrap_version': __version__
        }

    def run_interactive_setup(self) -> Dict[str, Any]:
        """Run interactive setup wizard"""
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🧬 ELLMa Bootstrap Wizard                                      ║
║                                                                  ║
║   Welcome! Let's set up your ELLMa agent for optimal            ║
║   performance on your system.                                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

ELLMa Version: {__version__}
System: {self.system_info['platform']}
Python: {self.system_info['python_version']}
Memory: {self.system_info['memory_total'] / (1024 ** 3):.1f} GB

""")

        config = {}

        # Model configuration
        print("🤖 Model Configuration")
        print("-" * 50)

        config['model'] = self._configure_model()

        # Evolution configuration
        print("\n🧬 Evolution Configuration")
        print("-" * 50)

        config['evolution'] = self._configure_evolution()

        # Modules configuration
        print("\n📦 Modules Configuration")
        print("-" * 50)

        config['modules'] = self._configure_modules()

        # Logging configuration
        print("\n📝 Logging Configuration")
        print("-" * 50)

        config['logging'] = self._configure_logging()

        # Security configuration
        print("\n🔒 Security Configuration")
        print("-" * 50)

        config['security'] = self._configure_security()

        return config

    def _configure_model(self) -> Dict[str, Any]:
        """Configure model settings"""
        model_config = {}

        # Model path
        print("Where should ELLMa look for language models?")
        print(f"Default: {self.models_dir}")
        model_path = input("Model directory [default]: ").strip()

        if not model_path:
            model_path = str(self.models_dir)

        model_config['path'] = str(Path(model_path) / "mistral-7b.gguf")

        # Context length
        print("\nModel context length (number of tokens)?")
        print("- 2048: Faster, less memory")
        print("- 4096: Balanced (recommended)")
        print("- 8192: Slower, more memory")

        context_options = {'1': 2048, '2': 4096, '3': 8192}
        choice = input("Choose [1/2/3] (default: 2): ").strip() or '2'
        model_config['context_length'] = context_options.get(choice, 4096)

        # CPU threads
        cpu_count = self.system_info['cpu_count']
        print(f"\nNumber of CPU threads to use? (Available: {cpu_count})")
        threads = input(f"Threads [default: {cpu_count}]: ").strip()

        try:
            model_config['threads'] = int(threads) if threads else cpu_count
        except ValueError:
            model_config['threads'] = cpu_count

        # Temperature
        print("\nModel creativity level (temperature)?")
        print("- 0.3: Conservative, focused")
        print("- 0.7: Balanced (recommended)")
        print("- 1.0: Creative, varied")

        temp_options = {'1': 0.3, '2': 0.7, '3': 1.0}
        choice = input("Choose [1/2/3] (default: 2): ").strip() or '2'
        model_config['temperature'] = temp_options.get(choice, 0.7)

        return model_config

    def _configure_evolution(self) -> Dict[str, Any]:
        """Configure evolution settings"""
        evolution_config = {}

        print("Enable automatic self-evolution?")
        print("This allows ELLMa to improve itself over time.")

        enable = input("Enable evolution? [Y/n]: ").strip().lower()
        evolution_config['enabled'] = enable not in ['n', 'no', 'false']

        if evolution_config['enabled']:
            print("\nEnable automatic improvements?")
            print("ELLMa will automatically create new capabilities.")

            auto = input("Auto-improve? [Y/n]: ").strip().lower()
            evolution_config['auto_improve'] = auto not in ['n', 'no', 'false']

            print("\nEvolution frequency?")
            print("How often should ELLMa evolve (commands between cycles)?")

            freq_options = {'1': 25, '2': 50, '3': 100}
            choice = input("Choose [1: Often/2: Normal/3: Rarely] (default: 2): ").strip() or '2'
            evolution_config['evolution_interval'] = freq_options.get(choice, 50)
        else:
            evolution_config['auto_improve'] = False
            evolution_config['evolution_interval'] = 100

        evolution_config['learning_rate'] = 0.1
        evolution_config['max_modules'] = 100
        evolution_config['backup_before_evolution'] = True

        return evolution_config

    def _configure_modules(self) -> Dict[str, Any]:
        """Configure modules settings"""
        modules_config = {}

        print("Module loading preferences:")

        # Auto-load modules
        auto_load = input("Auto-load available modules? [Y/n]: ").strip().lower()
        modules_config['auto_load'] = auto_load not in ['n', 'no', 'false']

        # Custom modules path
        print(f"\nCustom modules directory: {self.modules_dir}")
        custom_path = input("Custom path [default]: ").strip()
        modules_config['custom_path'] = custom_path or str(self.modules_dir)

        # Built-in modules
        builtin = input("Load built-in modules? [Y/n]: ").strip().lower()
        modules_config['builtin_modules'] = builtin not in ['n', 'no', 'false']

        modules_config['allow_remote'] = False  # Security: disabled by default

        return modules_config

    def _configure_logging(self) -> Dict[str, Any]:
        """Configure logging settings"""
        logging_config = {}

        print("Logging level:")
        print("- DEBUG: Very detailed (for development)")
        print("- INFO: Normal information (recommended)")
        print("- WARNING: Only warnings and errors")

        level_options = {'1': 'DEBUG', '2': 'INFO', '3': 'WARNING'}
        choice = input("Choose [1/2/3] (default: 2): ").strip() or '2'
        logging_config['level'] = level_options.get(choice, 'INFO')

        # Log to file
        log_file = input("Enable file logging? [Y/n]: ").strip().lower()
        if log_file not in ['n', 'no', 'false']:
            logging_config['file'] = str(self.logs_dir / "ellma.log")
        else:
            logging_config['file'] = None

        logging_config['console'] = True
        logging_config['max_size'] = "10MB"
        logging_config['backup_count'] = 5

        return logging_config

    def _configure_security(self) -> Dict[str, Any]:
        """Configure security settings"""
        security_config = {}

        print("Security settings:")

        # Sandbox mode
        sandbox = input("Enable sandbox mode? (restricts file access) [y/N]: ").strip().lower()
        security_config['sandbox_mode'] = sandbox in ['y', 'yes', 'true']

        # Execution timeout
        print("\nMaximum command execution time (seconds)?")
        timeout = input("Timeout [300]: ").strip()

        try:
            security_config['max_execution_time'] = int(timeout) if timeout else 300
        except ValueError:
            security_config['max_execution_time'] = 300

        # Confirmation for dangerous operations
        confirm = input("Require confirmation for dangerous operations? [Y/n]: ").strip().lower()
        security_config['require_confirmation'] = confirm not in ['n', 'no', 'false']

        security_config['allowed_commands'] = None
        security_config['blocked_commands'] = None

        return security_config

    def create_directories(self):
        """Create necessary directories"""
        logger.info("Creating ELLMa directories...")

        directories = [
            self.home_dir,
            self.models_dir,
            self.modules_dir,
            self.logs_dir,
            self.home_dir / "evolution",
            self.home_dir / "config"
        ]

        for directory in directories:
            ensure_directory(directory)
            logger.debug(f"Created directory: {directory}")

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        logger.info(f"Saving configuration to {self.config_file}")

        # Add bootstrap metadata
        config['bootstrap'] = self.bootstrap_config

        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, indent=2, default_flow_style=False)

        logger.info("Configuration saved successfully")

    def download_model(self, force: bool = False) -> bool:
        """Download default model if not present"""
        model_file = self.models_dir / "mistral-7b.gguf"

        if model_file.exists() and not force:
            logger.info(f"Model already exists: {model_file}")
            return True

        print("\n📥 Downloading Mistral 7B model...")
        print("This may take several minutes depending on your connection.")

        model_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

        try:
            import urllib.request
            from urllib.error import URLError

            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(downloaded * 100 / total_size, 100)
                    print(f"\rProgress: {percent:.1f}% ({downloaded // (1024 * 1024)} MB)", end='', flush=True)

            urllib.request.urlretrieve(model_url, model_file, progress_hook)
            print(f"\n✅ Model downloaded: {model_file}")
            return True

        except URLError as e:
            logger.error(f"Failed to download model: {e}")
            print(f"\n❌ Download failed. You can download manually:")
            print(f"URL: {model_url}")
            print(f"Save to: {model_file}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading model: {e}")
            return False

    def test_installation(self) -> bool:
        """Test ELLMa installation"""
        logger.info("Testing ELLMa installation...")

        try:
            # Test basic import
            agent = ELLMa(config_path=str(self.config_file))

            # Test basic command
            status = agent.get_status()

            print(f"\n✅ ELLMa test successful!")
            print(f"Version: {status['version']}")
            print(f"Model loaded: {'Yes' if status['model_loaded'] else 'No'}")
            print(f"Modules: {status['modules_count']}")
            print(f"Commands: {status['commands_count']}")

            return True

        except Exception as e:
            logger.error(f"ELLMa test failed: {e}")
            print(f"\n❌ ELLMa test failed: {e}")
            return False

    def create_example_module(self):
        """Create an example custom module"""
        example_module = self.modules_dir / "example_module.py"

        if example_module.exists():
            return

        module_code = '''"""
Example ELLMa Module

This is an example of how to create custom modules for ELLMa.
"""

from ellma.commands.base import BaseCommand

class ExampleCommands(BaseCommand):
    """Example command module for ELLMa"""

    def __init__(self, agent):
        super().__init__(agent)
        self.name = "example"
        self.description = "Example commands for demonstration"

    def hello(self, name: str = "World") -> str:
        """
        Say hello to someone

        Args:
            name: Name to greet

        Returns:
            Greeting message
        """
        return f"Hello, {name}! This is from the example module."

    def calculate(self, expression: str) -> str:
        """
        Safely calculate mathematical expressions

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Calculation result
        """
        try:
            # Simple evaluation for demo (in production, use safer methods)
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"{expression} = {result}"
            else:
                return "Error: Invalid characters in expression"
        except Exception as e:
            return f"Error: {e}"

    def system_info(self) -> dict:
        """Get basic system information"""
        import platform
        import psutil

        return {
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "python_version": platform.python_version()
        }
'''

        with open(example_module, 'w') as f:
            f.write(module_code)

        logger.info(f"Created example module: {example_module}")

    def show_next_steps(self):
        """Show next steps to the user"""
        print(f"""
🎉 ELLMa Bootstrap Complete!

Your ELLMa agent is ready to use. Here's what you can do next:

📍 Quick Start:
   ellma shell                    # Start interactive shell
   ellma exec "system.scan"       # Scan your system
   ellma exec "example.hello"     # Try the example module

🔧 Configuration:
   Config file: {self.config_file}
   Models dir:  {self.models_dir}
   Modules dir: {self.modules_dir}

🧬 Evolution:
   ellma evolve                   # Trigger manual evolution
   ellma status                   # Check agent status

📚 Learn More:
   ellma --help                   # Show all commands
   ellma shell                    # Interactive exploration

🎯 Next Steps:
   1. Try the interactive shell: ellma shell
   2. Explore built-in commands: help
   3. Let ELLMa evolve: ellma evolve
   4. Create custom modules in: {self.modules_dir}

Happy coding with ELLMa! 🚀
""")


def main():
    """Main bootstrap function"""
    parser = argparse.ArgumentParser(description="Bootstrap ELLMa agent")
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run interactive setup wizard')
    parser.add_argument('--download-model', '-d', action='store_true',
                        help='Download default model')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force overwrite existing configuration')
    parser.add_argument('--config-file', '-c', type=str,
                        help='Custom configuration file path')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress output')

    args = parser.parse_args()

    if args.quiet:
        setup_logging(level='WARNING', console=True)

    # Initialize bootstrap
    bootstrap = ELLMaBootstrap()

    if args.config_file:
        bootstrap.config_file = Path(args.config_file)

    # Check if already configured
    if bootstrap.config_file.exists() and not args.force:
        print(f"ELLMa already configured: {bootstrap.config_file}")
        print("Use --force to overwrite or --interactive to reconfigure")
        return

    try:
        # Create directories
        bootstrap.create_directories()

        # Configuration
        if args.interactive:
            config = bootstrap.run_interactive_setup()
        else:
            # Use default configuration
            from ellma.utils.config import ConfigManager
            manager = ConfigManager()
            config = manager.get_config()

        # Save configuration
        bootstrap.save_config(config)

        # Download model if requested
        if args.download_model:
            bootstrap.download_model()

        # Create example module
        bootstrap.create_example_module()

        # Test installation
        if bootstrap.test_installation():
            bootstrap.show_next_steps()

    except KeyboardInterrupt:
        print("\n\nBootstrap cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()