"""
ELLMa Base Command Class

This module provides the base class for all ELLMa commands with common
functionality, validation, and error handling patterns.
"""

import time
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Type, TypeVar

from ellma.utils.logger import get_logger
from ellma.utils.error_logger import log_command_error

logger = get_logger(__name__)


class CommandError(Exception):
    """Base exception for command errors"""
    pass


class CommandValidationError(CommandError):
    """Exception for command validation errors"""
    pass


class CommandExecutionError(CommandError):
    """Exception for command execution errors"""
    pass


class CommandTimeoutError(CommandError):
    """Exception for command timeout errors"""
    pass


def validate_args(*arg_types, **kwarg_types):
    """Decorator for argument validation"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Validate positional arguments
            for i, (arg, expected_type) in enumerate(zip(args, arg_types)):
                if not isinstance(arg, expected_type):
                    raise CommandValidationError(
                        f"Argument {i} must be {expected_type.__name__}, got {type(arg).__name__}"
                    )

            # Validate keyword arguments
            for key, expected_type in kwarg_types.items():
                if key in kwargs and not isinstance(kwargs[key], expected_type):
                    raise CommandValidationError(
                        f"Argument '{key}' must be {expected_type.__name__}, got {type(kwargs[key]).__name__}"
                    )

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def timeout(seconds: int):
    """Decorator for command timeout"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise CommandTimeoutError(f"Command {func.__name__} timed out after {seconds} seconds")

            # Set timeout (Unix only)
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                try:
                    result = func(self, *args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

                return result
            except AttributeError:
                # Windows doesn't support SIGALRM, fallback to simple execution
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


def log_execution(func):
    """Decorator to log command execution"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        self.logger.info(f"Executing {func.__name__}")

        try:
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            self.logger.info(f"Command {func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Command {func.__name__} failed after {execution_time:.3f}s: {e}", exc_info=True)
            
            # Log to TODO file with additional context
            context = {
                'command': f"{getattr(self, 'name', self.__class__.__name__)}.{func.__name__}",
                'execution_time': f"{execution_time:.3f}s",
                'error_type': e.__class__.__name__,
                'error_details': str(e),
                'args': str(args),
                'kwargs': str(kwargs),
            }
            
            log_command_error(
                command=context['command'],
                error=e,
                context=context
            )
            raise

    return wrapper


class BaseCommand(ABC):
    """
    Base class for all ELLMa commands

    Provides common functionality including:
    - Agent reference
    - Command metadata
    - Execution logging
    - Error handling
    - Validation helpers
    """

    def __init__(self, agent):
        """
        Initialize base command

        Args:
            agent: ELLMa agent instance
        """
        self.agent = agent
        self.name = getattr(self, 'name', self.__class__.__name__.lower())
        self.description = getattr(self, 'description', self.__doc__ or "No description")
        self.version = getattr(self, 'version', "1.0.0")
        self.logger = get_logger(f"commands.{self.name}")

        # Command metadata
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution = None
        self.error_count = 0

        # Initialize command-specific setup
        self._initialize()

    def _initialize(self):
        """Override this method for command-specific initialization"""
        pass

    def get_commands(self) -> Dict[str, Any]:
        """
        Get available commands from this module

        Returns:
            Dictionary mapping command names to this instance
        """
        return {self.name: self}

    def get_actions(self) -> List[str]:
        """
        Get list of available actions (public methods)

        Returns:
            List of action names
        """
        actions = []
        for name in dir(self):
            if not name.startswith('_') and callable(getattr(self, name)):
                # Exclude base class methods
                if name not in ['get_commands', 'get_actions', 'get_help', 'get_metadata']:
                    actions.append(name)
        return actions

    def get_help(self, action: Optional[str] = None) -> str:
        """
        Get help information for command or specific action

        Args:
            action: Specific action to get help for

        Returns:
            Help text
        """
        if action is None:
            # General command help
            help_text = f"Command: {self.name}\n"
            help_text += f"Description: {self.description}\n"
            help_text += f"Version: {self.version}\n\n"
            help_text += "Available actions:\n"

            for action_name in self.get_actions():
                method = getattr(self, action_name)
                doc = method.__doc__ or "No description"
                help_text += f"  {action_name}: {doc.split('.')[0]}\n"

            return help_text
        else:
            # Specific action help
            if hasattr(self, action):
                method = getattr(self, action)
                help_text = f"Action: {self.name}.{action}\n"
                help_text += f"Description: {method.__doc__ or 'No description'}\n"

                # Get method signature
                sig = inspect.signature(method)
                help_text += f"Signature: {action}{sig}\n"

                return help_text
            else:
                return f"Action '{action}' not found in command '{self.name}'"

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get command metadata

        Returns:
            Metadata dictionary
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'actions': self.get_actions(),
            'execution_count': self.execution_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': (
                self.total_execution_time / self.execution_count
                if self.execution_count > 0 else 0
            ),
            'last_execution': self.last_execution,
            'error_count': self.error_count,
            'error_rate': (
                self.error_count / self.execution_count
                if self.execution_count > 0 else 0
            )
        }

    def _record_execution(self, duration: float, success: bool = True):
        """Record execution statistics"""
        self.execution_count += 1
        self.total_execution_time += duration
        self.last_execution = datetime.now().isoformat()

        if not success:
            self.error_count += 1

    def _validate_agent(self):
        """Validate that agent is available and configured"""
        if not self.agent:
            raise CommandError("Agent not available")

        if not hasattr(self.agent, 'llm'):
            raise CommandError("Agent LLM not configured")

    def _require_llm(self):
        """Require LLM to be loaded for this command"""
        self._validate_agent()

        if not self.agent.llm:
            raise CommandError("This command requires LLM model to be loaded")

    def _safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Safely execute a function with error handling and logging

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            self._record_execution(duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self._record_execution(duration, success=False)
            self.logger.error(f"Error in {func.__name__}: {e}")
            raise CommandExecutionError(f"Command execution failed: {e}")

    def _format_output(self, data: Any, format_type: str = "auto") -> str:
        """
        Format output data for display

        Args:
            data: Data to format
            format_type: Format type (auto, json, yaml, table)

        Returns:
            Formatted string
        """
        if format_type == "json" or (format_type == "auto" and isinstance(data, (dict, list))):
            import json
            return json.dumps(data, indent=2)

        elif format_type == "yaml":
            import yaml
            return yaml.dump(data, indent=2)

        elif format_type == "table" and isinstance(data, list):
            from rich.table import Table
            from rich.console import Console

            console = Console()
            table = Table()

            if data and isinstance(data[0], dict):
                # Add columns from first item keys
                for key in data[0].keys():
                    table.add_column(str(key))

                # Add rows
                for item in data:
                    table.add_row(*[str(item.get(key, '')) for key in data[0].keys()])

                with console.capture() as capture:
                    console.print(table)
                return capture.get()

        return str(data)

    def _get_user_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with prompt"""
        try:
            from rich.prompt import Prompt
            return Prompt.ask(prompt, default=default)
        except ImportError:
            # Fallback to basic input
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                return user_input if user_input else default
            else:
                return input(f"{prompt}: ").strip()

    def _confirm_action(self, message: str) -> bool:
        """Get user confirmation for action"""
        try:
            from rich.prompt import Confirm
            return Confirm.ask(message)
        except ImportError:
            # Fallback to basic input
            response = input(f"{message} (y/N): ").strip().lower()
            return response in ['y', 'yes']

    def _progress_bar(self, iterable, description: str = "Processing"):
        """Create progress bar for iterable"""
        try:
            from rich.progress import track
            return track(iterable, description=description)
        except ImportError:
            # Fallback without progress bar
            return iterable

    def _console_print(self, *args, **kwargs):
        """Print to console with rich formatting if available"""
        try:
            from rich.console import Console
            console = Console()
            console.print(*args, **kwargs)
        except ImportError:
            # Fallback to regular print
            print(*args)

    def __call__(self, action: str, *args, **kwargs):
        """Make command callable with action name"""
        try:
            if not hasattr(self, action):
                raise CommandError(f"Unknown action: {action}")

            method = getattr(self, action)
            if not callable(method):
                raise CommandError(f"{action} is not callable")

            return method(*args, **kwargs)
        except Exception as e:
            # Log the error to TODO file
            context = {
                'command': f"{self.name}.{action}",
                'args': str(args),
                'kwargs': str(kwargs),
                'error_type': e.__class__.__name__,
            }
            
            # Include more context for specific error types
            if isinstance(e, (CommandValidationError, CommandExecutionError, CommandTimeoutError)):
                context['error_details'] = str(e)
            
            log_command_error(
                command=f"{self.name}.{action}",
                error=e,
                context=context
            )
            raise


class SimpleCommand(BaseCommand):
    """
    Simple command implementation for quick command creation

    Example:
        def my_action(arg1, arg2="default"):
            return f"Result: {arg1}, {arg2}"

        command = SimpleCommand(agent, "mycommand", actions={"action": my_action})
    """

    def __init__(self, agent, name: str, description: str = "", actions: Dict[str, Callable] = None):
        """
        Initialize simple command

        Args:
            agent: ELLMa agent instance
            name: Command name
            description: Command description
            actions: Dictionary of action name -> function
        """
        self.name = name
        self.description = description
        self._actions = actions or {}

        # Dynamically add actions as methods
        for action_name, action_func in self._actions.items():
            setattr(self, action_name, action_func)

        super().__init__(agent)

    def get_actions(self) -> List[str]:
        """Get list of available actions"""
        return list(self._actions.keys())


# Utility functions for command development

def create_command_from_functions(agent, name: str, functions: Dict[str, Callable],
                                  description: str = "") -> SimpleCommand:
    """
    Create a command from a dictionary of functions

    Args:
        agent: ELLMa agent instance
        name: Command name
        functions: Dictionary of function name -> function
        description: Command description

    Returns:
        SimpleCommand instance
    """
    return SimpleCommand(agent, name, description, functions)


def command_registry(registry: Dict[str, BaseCommand]):
    """Decorator to register commands in a registry"""

    def decorator(cls):
        if hasattr(cls, 'name'):
            registry[cls.name] = cls
        else:
            registry[cls.__name__.lower()] = cls
        return cls

    return decorator


if __name__ == "__main__":
    # Example usage
    class ExampleCommand(BaseCommand):
        """Example command for testing"""

        def __init__(self, agent):
            self.name = "example"
            self.description = "Example command for demonstration"
            super().__init__(agent)

        @validate_args(str, int)
        @log_execution
        def test_action(self, text: str, number: int) -> Dict[str, Any]:
            """Test action with validation"""
            return {
                "input_text": text,
                "input_number": number,
                "result": f"Processed {text} with {number}"
            }

        @timeout(10)
        def slow_action(self):
            """Action that might timeout"""
            import time
            time.sleep(5)
            return "Completed"


    # Mock agent for testing
    class MockAgent:
        def __init__(self):
            self.llm = None


    agent = MockAgent()
    cmd = ExampleCommand(agent)

    print("Command metadata:")
    print(cmd.get_metadata())

    print("\nHelp:")
    print(cmd.get_help())

    print("\nTesting action:")
    result = cmd.test_action("hello", 42)
    print(result)

    print("\nUpdated metadata:")
    print(cmd.get_metadata())