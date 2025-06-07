"""
ELLMa Interactive Shell - Command Line Interface

This module provides an interactive shell interface for ELLMa that allows
users to execute commands, explore capabilities, and interact with the agent
in a natural, conversational way.
"""

import os
import sys
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from ellma.constants import BANNER
from ellma.utils.logger import get_logger

logger = get_logger(__name__)


class ELLMaCompleter(Completer):
    """Custom completer for ELLMa commands"""

    def __init__(self, agent):
        self.agent = agent
        self.commands = []
        self._update_commands()

    def _update_commands(self):
        """Update available commands"""
        self.commands = []

        # Add structured commands (module.action)
        for module_name, module in self.agent.commands.items():
            actions = [attr for attr in dir(module) if not attr.startswith('_') and callable(getattr(module, attr))]
            for action in actions:
                self.commands.append(f"{module_name}.{action}")

        # Add shell built-in commands
        shell_commands = [
            'help', 'status', 'evolve', 'reload', 'history',
            'clear', 'exit', 'quit', 'modules', 'config',
            'generate', 'analyze', 'monitor'
        ]
        self.commands.extend(shell_commands)

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()

        for command in self.commands:
            if command.startswith(word):
                yield Completion(command, start_position=-len(word))


class InteractiveShell:
    """
    Interactive Shell for ELLMa Agent

    Provides a rich, interactive command-line interface with:
    - Command completion
    - Command history
    - Natural language processing
    - Rich output formatting
    - Built-in help system
    """

    def __init__(self, agent):
        """
        Initialize Interactive Shell

        Args:
            agent: ELLMa agent instance
        """
        self.agent = agent
        self.console = Console()
        self.session_history = []
        self.running = True

        # Setup prompt toolkit components
        self.history_file = self.agent.home_dir / "shell_history.txt"
        self.history = FileHistory(str(self.history_file))
        self.completer = ELLMaCompleter(agent)

        # Shell style
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'path': '#884444',
            'time': '#888888',
        })

        # Built-in commands
        self.builtin_commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'evolve': self._cmd_evolve,
            'reload': self._cmd_reload,
            'history': self._cmd_history,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit,
            'modules': self._cmd_modules,
            'config': self._cmd_config,
            'generate': self._cmd_generate,
            'analyze': self._cmd_analyze,
            'monitor': self._cmd_monitor,
        }

    def run(self):
        """Start the interactive shell"""
        self.console.print(BANNER)
        self._cmd_status([])  # Show initial status

        while self.running:
            try:
                # Create prompt with current time and status
                current_time = datetime.now().strftime("%H:%M:%S")
                prompt_text = HTML(f'<time>{current_time}</time> <prompt>ellma></prompt> ')

                # Get user input
                user_input = prompt(
                    prompt_text,
                    history=self.history,
                    completer=self.completer,
                    style=self.style,
                    complete_while_typing=True
                ).strip()

                if not user_input:
                    continue

                # Log command
                self.session_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': user_input,
                    'type': 'user_input'
                })

                # Process command
                self._process_command(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' or 'quit' to leave the shell[/yellow]")
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Shell error: {e}[/red]")
                if self.agent.verbose:
                    self.console.print(traceback.format_exc())

        self._on_exit()

    def _process_command(self, user_input: str):
        """Process user command"""
        try:
            # Split command and arguments
            parts = user_input.split()
            command = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []

            # Check for built-in commands first
            if command in self.builtin_commands:
                result = self.builtin_commands[command](args)
                self._log_result(user_input, result, True)
                return

            # Check for structured commands (module.action)
            if '.' in command:
                result = self.agent.execute(user_input)
                self._display_result(result)
                self._log_result(user_input, result, True)
                return

            # Try as natural language command
            if self.agent.llm:
                self.console.print("[dim]Interpreting as natural language...[/dim]")
                result = self.agent.execute(user_input)
                self._display_result(result)
                self._log_result(user_input, result, True)
            else:
                self.console.print(f"[red]Unknown command: {command}[/red]")
                self.console.print("Type 'help' for available commands")
                self._log_result(user_input, f"Unknown command: {command}", False)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            self._log_result(user_input, str(e), False)

    def _display_result(self, result: Any):
        """Display command result with appropriate formatting"""
        if result is None:
            return

        if isinstance(result, dict):
            if 'error' in result:
                self.console.print(f"[red]Error: {result['error']}[/red]")
            else:
                table = Table(title="Result")
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="white")

                for key, value in result.items():
                    table.add_row(str(key), str(value))

                self.console.print(table)

        elif isinstance(result, list):
            if result:
                for i, item in enumerate(result, 1):
                    self.console.print(f"{i}. {item}")
            else:
                self.console.print("[dim]No results[/dim]")

        elif isinstance(result, str):
            # Try to detect and format code
            if 'def ' in result or 'class ' in result or '#!/bin/bash' in result:
                # Detect language
                if result.startswith('#!/bin/bash') or 'bash' in result.lower():
                    language = "bash"
                elif 'def ' in result or 'class ' in result:
                    language = "python"
                else:
                    language = "text"

                syntax = Syntax(result, language, theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title="Generated Code"))
            else:
                self.console.print(result)

        else:
            self.console.print(str(result))

    def _log_result(self, command: str, result: Any, success: bool):
        """Log command result"""
        self.session_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'result': str(result)[:500],  # Truncate long results
            'success': success,
            'type': 'result'
        })

    # Built-in Commands

    def _cmd_help(self, args: List[str]) -> str:
        """Show help information"""
        if args and args[0] in self.builtin_commands:
            # Show specific command help
            command = args[0]
            func = self.builtin_commands[command]
            return f"{command}: {func.__doc__}"

        # Show general help
        help_text = """
# ELLMa Interactive Shell Help

## Built-in Commands:
- **help** [command] - Show help (this message)
- **status** - Show agent status
- **evolve** - Trigger agent evolution
- **reload** - Reload modules
- **history** - Show command history
- **clear** - Clear screen
- **exit/quit** - Exit shell
- **modules** - List available modules
- **config** - Show configuration
- **generate** <type> <task> - Generate code
- **analyze** <target> - Analyze system/files
- **monitor** - Monitor system resources

## Module Commands:
Execute commands using format: `module.action [args]`

Available modules:
"""

        for module_name, module in self.agent.commands.items():
            actions = [attr for attr in dir(module) if not attr.startswith('_') and callable(getattr(module, attr))]
            help_text += f"- **{module_name}**: {', '.join(actions)}\n"

        help_text += """
## Natural Language:
You can also use natural language commands when LLM is loaded:
- "scan the system for issues"
- "read the latest news from hacker news"
- "generate a backup script"

## Examples:
```
system.scan
web.read https://example.com
generate python "web scraper"
evolve
```
"""

        markdown = Markdown(help_text)
        self.console.print(markdown)
        return "Help displayed"

    def _cmd_status(self, args: List[str]) -> Dict:
        """Show agent status"""
        status = self.agent.get_status()

        # Create status table
        table = Table(title="🤖 ELLMa Agent Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Version", status['version'])
        table.add_row("Model Loaded", "✅ Yes" if status['model_loaded'] else "❌ No")
        table.add_row("Model Path", status['model_path'] or "Not found")
        table.add_row("Modules", str(status['modules_count']))
        table.add_row("Commands", str(status['commands_count']))
        table.add_row("Commands Executed", str(status['performance_metrics']['commands_executed']))
        table.add_row("Success Rate",
                      f"{(status['performance_metrics']['successful_executions'] / max(status['performance_metrics']['commands_executed'], 1)) * 100:.1f}%")
        table.add_row("Evolution Cycles", str(status['performance_metrics']['evolution_cycles']))

        self.console.print(table)
        return status

    def _cmd_evolve(self, args: List[str]) -> Dict:
        """Trigger agent evolution"""
        if confirm("Start evolution process? This may take a few minutes."):
            return self.agent.evolve()
        return {"status": "cancelled"}

    def _cmd_reload(self, args: List[str]) -> str:
        """Reload modules"""
        self.agent.reload_modules()
        self.completer._update_commands()  # Update command completion
        return "Modules reloaded successfully"

    def _cmd_history(self, args: List[str]) -> str:
        """Show command history"""
        count = 20
        if args and args[0].isdigit():
            count = int(args[0])

        recent_history = self.session_history[-count:]

        table = Table(title=f"Last {len(recent_history)} Commands")
        table.add_column("Time", style="dim")
        table.add_column("Command", style="cyan")
        table.add_column("Status", style="white")

        for entry in recent_history:
            if entry['type'] == 'user_input':
                time_str = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
                # Find corresponding result
                result_entry = next(
                    (e for e in self.session_history
                     if e.get('command') == entry['command'] and e['type'] == 'result'),
                    None
                )
                status = "✅" if result_entry and result_entry.get('success') else "❌"
                table.add_row(time_str, entry['command'], status)

        self.console.print(table)
        return f"Showing {len(recent_history)} recent commands"

    def _cmd_clear(self, args: List[str]) -> str:
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        return "Screen cleared"

    def _cmd_exit(self, args: List[str]) -> str:
        """Exit shell"""
        self.running = False
        return "Goodbye!"

    def _cmd_modules(self, args: List[str]) -> str:
        """List available modules"""
        table = Table(title="📦 Available Modules")
        table.add_column("Module", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Actions", style="white")

        for module_name, module in self.agent.commands.items():
            actions = [attr for attr in dir(module) if not attr.startswith('_') and callable(getattr(module, attr))]
            module_type = "Built-in" if module_name in ['system', 'web', 'files'] else "Custom"
            table.add_row(module_name, module_type, ", ".join(actions[:3]) + ("..." if len(actions) > 3 else ""))

        self.console.print(table)
        return f"Total modules: {len(self.agent.commands)}"

    def _cmd_config(self, args: List[str]) -> Dict:
        """Show configuration"""
        config = self.agent.config

        # Format configuration nicely
        import json
        config_json = json.dumps(config, indent=2)
        syntax = Syntax(config_json, "json", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="Configuration"))

        return config

    def _cmd_generate(self, args: List[str]) -> str:
        """Generate code"""
        if len(args) < 2:
            return "Usage: generate <type> <task>\nTypes: python, bash, docker, groovy"

        code_type = args[0]
        task = " ".join(args[1:])

        # Use appropriate generator
        try:
            if code_type == "python":
                from ellma.generators.python import PythonGenerator
                generator = PythonGenerator(self.agent)
            elif code_type == "bash":
                from ellma.generators.bash import BashGenerator
                generator = BashGenerator(self.agent)
            elif code_type == "docker":
                from ellma.generators.docker import DockerGenerator
                generator = DockerGenerator(self.agent)
            else:
                return f"Unsupported code type: {code_type}"

            code = generator.generate(task)
            self._display_result(code)
            return f"Generated {code_type} code for: {task}"

        except ImportError:
            return f"Generator for {code_type} not available"
        except Exception as e:
            return f"Generation failed: {e}"

    def _cmd_analyze(self, args: List[str]) -> str:
        """Analyze system or files"""
        if not args:
            return "Usage: analyze <target>\nTargets: system, logs, performance"

        target = args[0]

        if target == "system":
            return self.agent.execute("system.scan")
        elif target == "logs":
            return self.agent.execute("files.analyze /var/log --pattern=error")
        elif target == "performance":
            return self.agent.get_status()['performance_metrics']
        else:
            return f"Unknown analysis target: {target}"

    def _cmd_monitor(self, args: List[str]) -> str:
        """Monitor system resources"""
        import psutil

        table = Table(title="🔍 System Monitor")
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="white")
        table.add_column("Status", style="white")

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 90 else "🔴"
        table.add_row("CPU", f"{cpu_percent}%", cpu_status)

        # Memory
        memory = psutil.virtual_memory()
        memory_status = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 90 else "🔴"
        table.add_row("Memory", f"{memory.percent}% ({memory.used // (1024 ** 3)}GB / {memory.total // (1024 ** 3)}GB)",
                      memory_status)

        # Disk
        disk = psutil.disk_usage('/')
        disk_status = "🟢" if disk.percent < 80 else "🟡" if disk.percent < 95 else "🔴"
        table.add_row("Disk", f"{disk.percent}% ({disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB)",
                      disk_status)

        # Network
        network = psutil.net_io_counters()
        network_status = "🟢" if network.bytes_recv < 1000000 else "🟡" if network.bytes_recv < 2000000 else "🔴"
        table.add_row("Network", f"{network.bytes_recv // (1024 ** 3)}MB / {network.bytes_sent // (1024 ** 3)}MB",
                      network_status)

        self.console.print(table)
        return "Monitoring system resources..."