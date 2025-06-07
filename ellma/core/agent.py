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
from ellma.utils.system import set_system_limits, get_system_status
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
        # Initialize basic attributes first
        self.console = Console()
        self.auto_evolve = auto_evolve
        self.verbose = verbose
        
        # Set system resource limits
        self.system_limits = set_system_limits()
        if self.verbose:
            self.console.print("[yellow]System limits set:[/yellow]")
            for k, v in self.system_limits.items():
                self.console.print(f"  - {k}: {v}")
            
            # Log system status
            status = get_system_status()
            if 'error' not in status:
                self.console.print("\n[yellow]System status:[/yellow]")
                self.console.print(f"  - CPU: {status['cpu']['percent']}% ({status['cpu']['count']} cores)")
                self.console.print(f"  - Memory: {status['memory']['percent']}% used ({status['memory']['available']/1024/1024:.1f}MB available)")
                self.console.print(f"  - Process threads: {status['process']['num_threads']}")
                self.console.print(f"  - Open files: {status['process']['open_files']}/{status['limits']['open_files'][0]}")
        
        # Initialize paths and directories
        self.home_dir = Path.home() / ".ellma"
        self.models_dir = self.home_dir / "models"
        self.modules_dir = self.home_dir / "modules"
        self.logs_dir = self.home_dir / "logs"
        
        # Ensure directories exist
        self._setup_directories()
        
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.config = {}
        
        # Set model path (either from parameter or auto-detect)
        self.model_path = Path(model_path) if model_path else None
        
        # Initialize LLM if model is available
        if self.model_path and self.model_path.exists():
            try:
                self._initialize_llm()
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                if "OMP" in str(e) or "thread" in str(e).lower():
                    logger.warning("This might be a threading issue. Try setting OMP_NUM_THREADS=1 in your environment.")
                raise
        else:
            logger.warning("No model loaded. Use 'load_model' to load a model.")
        
        # Now load the config which depends on model_path
        self._load_config()
        
        # If model_path wasn't provided or doesn't exist, try to find it
        if self.model_path is None or not self.model_path.exists():
            found_path = self._find_model()
            if found_path:
                self.model_path = Path(found_path)
        
        # Initialize other components
        self.module_registry = ModuleRegistry()
        self.llm = None
        self.commands = {}
        self.modules = {}
        self.task_history = []
        self.performance_metrics = {
            'commands_executed': 0,
            'successful_executions': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'evolution_cycles': 0
        }
        
        # Initialize the agent
        self._initialize()

    def _load_config(self):
        """Load configuration from config manager"""
        default_config = {
            'model': {
                'path': str(self.model_path) if self.model_path else None,
                'context_length': 2048,
                'n_threads': max(1, os.cpu_count() // 2)
            },
            'agent': {
                'auto_evolve': self.auto_evolve,
                'verbose': self.verbose
            },
            'directories': {
                'home': str(self.home_dir),
                'models': str(self.models_dir),
                'modules': str(self.modules_dir),
                'logs': str(self.logs_dir)
            },
            'logging': {
                'level': 'INFO',
                'system_log': str(self.logs_dir / 'system.log'),
                'chat_log': str(self.logs_dir / 'chat.log'),
                'max_size': '10MB',
                'backup_count': 5
            }
        }
        
        # Update with any existing config values
        for key in default_config:
            if isinstance(default_config[key], dict):
                for subkey in default_config[key]:
                    full_key = f"{key}.{subkey}"
                    value = self.config_manager.get(full_key, default_config[key][subkey])
                    if key not in self.config:
                        self.config[key] = {}
                    self.config[key][subkey] = value
            else:
                self.config[key] = self.config_manager.get(key, default_config[key])

    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.home_dir, self.models_dir, self.modules_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Configure logging for the agent"""
        from ellma.utils.logger import setup_logging
        
        # Get logging configuration
        log_config = self.config.get('logging', {})
        
        # Setup logging with both system and chat logs
        setup_logging(
            level=log_config.get('level', 'INFO'),
            log_file=log_config.get('system_log'),
            chat_log_file=log_config.get('chat_log'),
            max_size=log_config.get('max_size', '10MB'),
            backup_count=log_config.get('backup_count', 5),
            console=True,
            rich_console=True
        )
        
        # Log configuration details
        logger.debug("Logging configured with settings: %s", log_config)

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
            try:
                config_path = Path(self.config["model"]["path"]).expanduser().resolve()
                if config_path.exists():
                    logger.info(f"Found model in config: {config_path}")
                    return str(config_path)
            except Exception as e:
                logger.warning(f"Invalid model path in config: {e}")

        # Check possible locations
        for path in possible_paths:
            try:
                expanded_path = path.expanduser().resolve()
                if expanded_path.exists():
                    logger.info(f"Found model at: {expanded_path}")
                    return str(expanded_path)
            except Exception as e:
                logger.debug(f"Error checking path {path}: {e}")
                continue

        # No model found
        self.console.print("[yellow]⚠️  No LLM model found![/yellow]")
        self.console.print("Run: [bold]ellma setup --download-model[/bold] to download Mistral 7B")
        return None

    def _initialize(self):
        """Initialize the agent components"""
        # Setup logging first
        self._setup_logging()
        
        logger.info("Initializing ELLMa agent...")

        # Load LLM model
        if self.model_path and HAS_LLAMA_CPP:
            self._load_model()
        elif not HAS_LLAMA_CPP:
            logger.error("llama-cpp-python not installed!")
            self.console.print("[red]llama-cpp-python not installed![/red]")
            self.console.print("Install with: pip install llama-cpp-python")

        # Load modules and commands
        self._load_modules()
        self._register_commands()

        # Initialize performance tracking
        self._init_performance_tracking()
        
        logger.info("ELLMa agent initialization complete")

        logger.info("ELLMa agent initialized successfully")

    def _load_model(self):
        """Load the LLM model"""
        if not self.model_path or not self.model_path.exists():
            raise ModelNotFoundError(f"Model not found: {self.model_path}")

        try:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
            ) as progress:
                task = progress.add_task("Loading LLM model...", total=None)

                model_config = self.config.get("model", {})
                
                # Ensure model_path is a string and exists
                model_path_str = str(self.model_path.resolve())
                
                self.llm = Llama(
                    model_path=model_path_str,
                    n_ctx=model_config.get("context_length", 4096),
                    n_threads=model_config.get("threads", os.cpu_count()),
                    verbose=self.verbose
                )

                progress.update(task, description="Model loaded successfully!")

            self.console.print(f"[green]✅ Model loaded: {self.model_path.name}[/green]")
            logger.info(f"LLM model loaded: {self.model_path}")

        except Exception as e:
            logger.error(f"Error loading model {self.model_path}: {str(e)}", exc_info=True)
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

    def _parse_command_args(self, command_args: str) -> tuple[list, dict]:
        """Parse command line arguments into positional and keyword arguments
        
        Args:
            command_args: Raw command arguments as string
            
        Returns:
            tuple: (positional_args, keyword_args)
        """
        import shlex
        from typing import List, Dict, Any
        
        if not command_args.strip():
            return [], {}
            
        # Parse arguments using shlex to handle quoted strings properly
        try:
            args = shlex.split(command_args)
        except ValueError as e:
            raise CommandError(f"Error parsing arguments: {e}")
        
        positional = []
        keyword_args = {}
        i = 0
        
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Handle --flag=value or --flag value
                if '=' in arg:
                    key, value = arg[2:].split('=', 1)
                    keyword_args[key.replace('-', '_')] = self._convert_arg_value(value)
                else:
                    key = arg[2:].replace('-', '_')
                    # Check if next arg is a value (not another flag)
                    if i + 1 < len(args) and not args[i + 1].startswith('--'):
                        keyword_args[key] = self._convert_arg_value(args[i + 1])
                        i += 1  # Skip the next argument
                    else:
                        # Boolean flag (present = True)
                        keyword_args[key] = True
            else:
                positional.append(self._convert_arg_value(arg))
            i += 1
            
        return positional, keyword_args
        
    def _convert_arg_value(self, value: str) -> Any:
        """Convert string argument to appropriate Python type"""
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.lower() == 'none' or value.lower() == 'null':
            return None
            
        # Try to convert to int or float
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def _execute_structured_command(self, command: str, *args, **kwargs) -> Any:
        """Execute structured command (module.action format)"""
        # Split command into parts and arguments
        parts = command.split(' ', 1)
        command_part = parts[0]
        command_args = parts[1] if len(parts) > 1 else ""
        
        # Split module.action
        module_action = command_part.split('.')
        if len(module_action) != 2:
            raise CommandError("Command format must be 'module.action [arguments]'")

        module_name, action = module_action

        if module_name not in self.commands:
            raise CommandError(f"Module '{module_name}' not found. Available: {list(self.commands.keys())}")

        module = self.commands[module_name]
        if not hasattr(module, action):
            available_actions = [attr for attr in dir(module) if not attr.startswith('_')]
            raise CommandError(f"Action '{action}' not found in module '{module_name}'. Available: {available_actions}")

        # Get the method
        method = getattr(module, action)
        
        # Parse command line arguments
        if command_args:
            positional_args, keyword_args = self._parse_command_args(command_args)
            # Update kwargs with parsed keyword arguments
            kwargs.update(keyword_args)
            return method(*positional_args, **kwargs)
            
        return method(*args, **kwargs)

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
        """
        Determine if evolution should be triggered based on performance metrics.
        
        Returns:
            bool: True if evolution should be triggered, False otherwise
        """
        # Evolution triggers configuration
        commands_threshold = 50
        failure_rate_threshold = 0.2
        min_commands_for_failure_check = 10
        
        # Log current metrics
        logger.debug("🔍 Checking evolution conditions...")
        logger.debug(f"📊 Current metrics - Commands: {self.performance_metrics['commands_executed']}, "
                   f"Success: {self.performance_metrics['successful_executions']}, "
                   f"Failures: {self.performance_metrics.get('failed_executions', 0)}")
        
        # Check command count threshold
        commands_executed = self.performance_metrics['commands_executed']
        if commands_executed > 0 and commands_executed % commands_threshold == 0:
            logger.info(f"✅ Evolution triggered: Reached {commands_executed} commands (threshold: {commands_threshold})")
            return True
            
        # Check failure rate if we have enough commands for meaningful statistics
        total_executions = (self.performance_metrics['successful_executions'] +
                          self.performance_metrics.get('failed_executions', 0))
                          
        if total_executions >= min_commands_for_failure_check:
            failure_rate = self.performance_metrics.get('failed_executions', 0) / total_executions
            logger.debug(f"📉 Current failure rate: {failure_rate:.1%} (threshold: {failure_rate_threshold:.1%})")
            
            if failure_rate > failure_rate_threshold:
                logger.warning(f"⚠️  Evolution triggered: High failure rate {failure_rate:.1%} "
                            f"(threshold: {failure_rate_threshold:.1%})")
                return True
        
        logger.debug("ℹ️  Evolution not triggered - conditions not met")
        return False

    def _trigger_evolution(self):
        """Trigger automatic evolution"""
        logger.info("🔍 Starting automatic evolution process...")
        start_time = time.time()
        
        try:
            from ellma.core.evolution import EvolutionEngine
            
            logger.info("🔄 Initializing Evolution Engine...")
            evolution = EvolutionEngine(self)
            
            # Log evolution configuration
            logger.info(f"📊 Evolution configuration: {evolution.get_config() if hasattr(evolution, 'get_config') else 'Not available'}")
            
            logger.info("🚀 Starting evolution...")
            result = evolution.evolve()
            
            # Log evolution results
            duration = time.time() - start_time
            logger.info(f"✅ Evolution completed successfully in {duration:.2f} seconds")
            
            if isinstance(result, dict):
                logger.info("📋 Evolution summary:")
                for key, value in result.items():
                    logger.info(f"   • {key}: {value}")
            
            return result
            
        except ImportError as e:
            error_msg = f"❌ Failed to import EvolutionEngine: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
            
        except Exception as e:
            error_msg = f"❌ Auto-evolution failed after {time.time() - start_time:.2f}s: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def evolve(self, verbose: bool = True) -> Dict:
        """
        Manually trigger evolution process

        Args:
            verbose: If True, print detailed progress information

        Returns:
            Dict containing evolution results and statistics

        Raises:
            RuntimeError: If evolution fails
        """
        if verbose:
            logger.info("🔍 Starting manual evolution process...")
            logger.info("This process will analyze the current state and generate improvements")
        
        try:
            from ellma.core.evolution import EvolutionEngine
            
            if verbose:
                logger.info("🔄 Initializing Evolution Engine...")
                
            evolution = EvolutionEngine(self)
            
            if verbose:
                config = evolution.get_config() if hasattr(evolution, 'get_config') else {}
                logger.info(f"📊 Evolution configuration: {config}")
                logger.info("🚀 Beginning evolution process...")
                
            result = evolution.evolve()
            
            if verbose and isinstance(result, dict):
                logger.info("✅ Evolution completed successfully!")
                logger.info("📋 Results summary:")
                for key, value in result.items():
                    if isinstance(value, (str, int, float, bool)):
                        logger.info(f"   • {key}: {value}")
                    elif value is not None:
                        logger.info(f"   • {key}: {type(value).__name__}")
            
            return result
            
        except ImportError as e:
            error_msg = "❌ Failed to import EvolutionEngine. Make sure all dependencies are installed."
            logger.error(error_msg)
            if verbose:
                logger.error(f"Error details: {str(e)}")
            raise RuntimeError(error_msg) from e
            
        except Exception as e:
            error_msg = "❌ Evolution process failed"
            logger.error(error_msg)
            if verbose:
                logger.error(f"Error details: {str(e)}", exc_info=True)
            raise RuntimeError(f"{error_msg}: {str(e)}") from e

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
            'model_path': str(self.model_path) if self.model_path else None,
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