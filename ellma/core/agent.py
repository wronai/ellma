"""
ELLMa Core Agent - Main AI Agent Implementation

This module contains the core ELLMa agent that orchestrates all functionality
including LLM inference, command execution, module management, and evolution.
"""

import os
import json
import yaml
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import psutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ellma import ELLMaError, ModelNotFoundError, ModuleLoadError, CommandError
from ellma.utils.logger import get_logger
from ellma.utils.config import ConfigManager
from ellma.modules.registry import ModuleRegistry
from ellma.commands.base import BaseCommand

try:
    from llama_cpp import Llama

    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False
    Llama = None

logger = get_logger(__name__)


class ELLMa:
    """
    Main ELLMa Agent Class

    The central orchestrator for all ELLMa functionality including:
    - LLM model management and inference
    - Command execution and routing
    - Module loading and management  
    - Evolution and self-improvement
    - System integration and monitoring
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 config_path: Optional[str] = None,
                 auto_evolve: bool = True,
                 verbose: bool = False):
        """
        Initialize ELLMa Agent

        Args:
            model_path: Path to LLM model file (GGUF format)
            config_path: Path to configuration file
            auto_evolve: Enable automatic evolution
            verbose: Enable verbose logging
        """
        # Initialize console for rich output
        self.console = Console()

        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.module_registry = ModuleRegistry()

        # Agent state
        self.model_path = model_path or self._find_model()
        self.llm = None
        self.commands = {}
        self.modules = {}
        self.task_history = []
        self.performance_metrics = {}
        self.auto_evolve = auto_evolve
        self.verbose = verbose

        # Directories
        self.home_dir = Path.home() / ".ellma"
        self.models_dir = self.home_dir / "models"
        self.modules_dir = self.home_dir / "modules"
        self.logs_dir = self.home_dir / "logs"

        # Create directories
        self._setup_directories()

        # Initialize agent
        self._initialize()

    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.home_dir, self.models_dir, self.modules_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _find_model(self) -> Optional[str]:
        """Find available LLM model"""
        possible_paths = [
            self.models_dir / "mistral-7b.gguf",
            self.models_dir / "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            Path("./models/mistral-7b.gguf"),
            Path("/app/models/mistral-7b.gguf"),
        ]

        # Check config first
        if self.config.get("model", {}).get("path"):
            config_path = Path(self.config["model"]["path"]).expanduser()
            if config_path.exists():
                return str(config_path)

        # Check possible locations
        for path in possible_paths:
            expanded_path = path.expanduser()
            if expanded_path.exists():
                logger.info(f"Found model at: {expanded_path}")
                return str(expanded_path)

        # No model found
        self.console.print("[yellow]⚠️  No LLM model found![/yellow]")
        self.console.print("Run: [bold]ellma setup --download-model[/bold] to download Mistral 7B")
        return None

    def _initialize(self):
        """Initialize the agent components"""
        logger.info("Initializing ELLMa agent...")

        # Load LLM model
        if self.model_path and HAS_LLAMA_CPP:
            self._load_model()
        elif not HAS_LLAMA_CPP:
            self.console.print("[red]llama-cpp-python not installed![/red]")
            self.console.print("Install with: pip install llama-cpp-python")

        # Load modules and commands
        self._load_modules()
        self._register_commands()

        # Initialize performance tracking
        self._init_performance_tracking()

        logger.info("ELLMa agent initialized successfully")

    def _load_model(self):
        """Load the LLM model"""
        if not self.model_path or not Path(self.model_path).exists():
            raise ModelNotFoundError(f"Model not found: {self.model_path}")

        try:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
            ) as progress:
                task = progress.add_task("Loading LLM model...", total=None)

                model_config = self.config.get("model", {})
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=model_config.get("context_length", 4096),
                    n_threads=model_config.get("threads", os.cpu_count()),
                    verbose=self.verbose
                )

                progress.update(task, description="Model loaded successfully!")

            self.console.print(f"[green]✅ Model loaded: {Path(self.model_path).name}[/green]")
            logger.info(f"LLM model loaded: {self.model_path}")

        except Exception as e:
            raise ModelNotFoundError(f"Failed to load model: {e}")

    def _load_modules(self):
        """Load available modules"""
        try:
            self.modules = self.module_registry.load_all_modules(self.modules_dir)
            if self.modules:
                logger.info(f"Loaded {len(self.modules)} modules")
        except Exception as e:
            logger.error(f"Failed to load modules: {e}")

    def _register_commands(self):
        """Register built-in and module commands"""
        # Import built-in commands
        try:
            from ellma.commands.system import SystemCommands
            from ellma.commands.web import WebCommands
            from ellma.commands.files import FileCommands

            self.commands.update({
                'system': SystemCommands(self),
                'web': WebCommands(self),
                'files': FileCommands(self)
            })

            # Register module commands
            for module_name, module in self.modules.items():
                if hasattr(module, 'get_commands'):
                    self.commands.update(module.get_commands())

            logger.info(f"Registered {len(self.commands)} command modules")

        except ImportError as e:
            logger.warning(f"Failed to import some commands: {e}")

    def _init_performance_tracking(self):
        """Initialize performance tracking"""
        self.performance_metrics = {
            'commands_executed': 0,
            'total_execution_time': 0.0,
            'successful_executions': 0,
            'failed_executions': 0,
            'evolution_cycles': 0,
            'modules_created': 0,
            'system_resources': {
                'cpu_usage': [],
                'memory_usage': [],
                'disk_usage': []
            }
        }

        # Load existing metrics if available
        metrics_file = self.home_dir / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    self.performance_metrics.update(saved_metrics)
            except Exception as e:
                logger.warning(f"Failed to load performance metrics: {e}")

    def execute(self, command: str, *args, **kwargs) -> Any:
        """
        Execute a command

        Args:
            command: Command in format 'module.action' or natural language
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Command execution result

        Raises:
            CommandError: If command execution fails
        """
        start_time = time.time()

        try:
            # Update metrics
            self.performance_metrics['commands_executed'] += 1

            # Parse command
            if '.' in command:
                # Structured command: module.action
                result = self._execute_structured_command(command, *args, **kwargs)
            else:
                # Natural language command
                result = self._execute_natural_command(command, *args, **kwargs)

            # Record success
            execution_time = time.time() - start_time
            self.performance_metrics['successful_executions'] += 1
            self.performance_metrics['total_execution_time'] += execution_time

            # Log task for evolution
            self._log_task(command, args, kwargs, result, execution_time, True)

            # Auto-evolve if enabled
            if self.auto_evolve and self._should_evolve():
                self._trigger_evolution()

            return result

        except Exception as e:
            # Record failure
            execution_time = time.time() - start_time
            self.performance_metrics['failed_executions'] += 1
            self.performance_metrics['total_execution_time'] += execution_time

            # Log failed task
            self._log_task(command, args, kwargs, str(e), execution_time, False)

            raise CommandError(f"Command execution failed: {e}")

    def _execute_structured_command(self, command: str, *args, **kwargs) -> Any:
        """Execute structured command (module.action format)"""
        parts = command.split('.')
        if len(parts) != 2:
            raise CommandError("Command format must be 'module.action'")

        module_name, action = parts

        if module_name not in self.commands:
            raise CommandError(f"Module '{module_name}' not found. Available: {list(self.commands.keys())}")

        module = self.commands[module_name]
        if not hasattr(module, action):
            available_actions = [attr for attr in dir(module) if not attr.startswith('_')]
            raise CommandError(f"Action '{action}' not found in module '{module_name}'. Available: {available_actions}")

        return getattr(module, action)(*args, **kwargs)

    def _execute_natural_command(self, command: str, *args, **kwargs) -> Any:
        """Execute natural language command using LLM"""
        if not self.llm:
            raise CommandError("LLM model not loaded for natural language commands")

        # Generate structured command from natural language
        prompt = f"""
        Convert this natural language command to a structured command:
        "{command}"

        Available modules and actions:
        {self._get_available_commands()}

        Return only the structured command in format 'module.action' with parameters.
        If the command is unclear, suggest the closest match.
        """

        try:
            response = self.generate(prompt, max_tokens=100)
            structured_command = response.strip()

            # Execute the generated structured command
            self.console.print(f"[dim]Executing: {structured_command}[/dim]")
            return self._execute_structured_command(structured_command, *args, **kwargs)

        except Exception as e:
            raise CommandError(f"Failed to interpret natural language command: {e}")

    def _get_available_commands(self) -> str:
        """Get formatted list of available commands"""
        commands_info = []
        for module_name, module in self.commands.items():
            actions = [attr for attr in dir(module) if not attr.startswith('_') and callable(getattr(module, attr))]
            commands_info.append(f"{module_name}: {', '.join(actions)}")
        return '\n'.join(commands_info)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using LLM

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters

        Returns:
            Generated text response
        """
        if not self.llm:
            raise ModelNotFoundError("LLM model not loaded")

        # Default parameters from config
        model_config = self.config.get("model", {})
        generation_params = {
            'max_tokens': kwargs.get('max_tokens', 512),
            'temperature': kwargs.get('temperature', model_config.get('temperature', 0.7)),
            'top_p': kwargs.get('top_p', model_config.get('top_p', 0.9)),
            'stop': kwargs.get('stop', [])
        }

        try:
            response = self.llm(prompt, **generation_params)
            return response['choices'][0]['text'].strip()
        except Exception as e:
            raise ELLMaError(f"LLM generation failed: {e}")

    def _log_task(self, command: str, args: tuple, kwargs: dict,
                  result: Any, execution_time: float, success: bool):
        """Log task execution for evolution"""
        task_log = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'args': str(args),
            'kwargs': str(kwargs),
            'result': str(result)[:500],  # Truncate long results
            'execution_time': execution_time,
            'success': success,
            'system_state': self._get_system_state()
        }

        self.task_history.append(task_log)

        # Keep only last 1000 tasks to manage memory
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]

    def _get_system_state(self) -> Dict:
        """Get current system state"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception:
            return {}

    def _should_evolve(self) -> bool:
        """Determine if evolution should be triggered"""
        # Evolution triggers
        commands_threshold = 50
        failure_rate_threshold = 0.2
        time_since_last_evolution = 3600  # 1 hour

        # Check command count
        if self.performance_metrics['commands_executed'] % commands_threshold == 0:
            return True

        # Check failure rate
        total_executions = (self.performance_metrics['successful_executions'] +
                            self.performance_metrics['failed_executions'])
        if total_executions > 10:
            failure_rate = self.performance_metrics['failed_executions'] / total_executions
            if failure_rate > failure_rate_threshold:
                return True

        return False

    def _trigger_evolution(self):
        """Trigger automatic evolution"""
        try:
            from ellma.core.evolution import EvolutionEngine
            evolution = EvolutionEngine(self)
            evolution.evolve()
        except Exception as e:
            logger.error(f"Auto-evolution failed: {e}")

    def evolve(self) -> Dict:
        """
        Manually trigger evolution process

        Returns:
            Evolution results
        """
        from ellma.core.evolution import EvolutionEngine
        evolution = EvolutionEngine(self)
        return evolution.evolve()

    def shell(self):
        """Start interactive shell"""
        from ellma.core.shell import InteractiveShell
        shell = InteractiveShell(self)
        shell.run()

    def get_status(self) -> Dict:
        """Get agent status information"""
        return {
            'version': '0.1.6',
            'model_loaded': self.llm is not None,
            'model_path': self.model_path,
            'modules_count': len(self.modules),
            'commands_count': len(self.commands),
            'performance_metrics': self.performance_metrics.copy(),
            'config': self.config
        }

    def save_state(self):
        """Save agent state to disk"""
        try:
            # Save performance metrics
            metrics_file = self.home_dir / "metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)

            # Save task history
            history_file = self.home_dir / "task_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.task_history[-100:], f, indent=2)  # Save last 100 tasks

            logger.info("Agent state saved successfully")

        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")

    def reload_modules(self):
        """Reload all modules"""
        self.modules = {}
        self.commands = {}
        self._load_modules()
        self._register_commands()
        self.console.print("[green]✅ Modules reloaded successfully[/green]")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save state"""
        self.save_state()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.save_state()
        except Exception:
            pass  # Ignore errors during cleanup