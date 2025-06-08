"""
ELLMa Introspection Commands

This module provides comprehensive system introspection capabilities including:
- Viewing and searching source code
- Inspecting configuration
- System information and diagnostics
- Module and command exploration
"""

import os
import sys
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax

from ellma.commands.base import BaseCommand
from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class IntrospectionCommands(BaseCommand):
    """System introspection and diagnostics commands"""
    
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "sys"
        self.description = "System introspection and diagnostics"
        self.console = Console()
        
        # Command mapping for NLP matching
        self._command_map = self._build_command_map()
    
    def _build_command_map(self) -> Dict[str, List[str]]:
        """Build a mapping of keywords to command methods"""
        return {
            # Configuration
            'config': ['show_config', 'get_config', 'settings'],
            'setting': ['show_config', 'get_config'],
            'parameter': ['show_config'],
            
            # Source code
            'source': ['show_source', 'view_code'],
            'code': ['show_source', 'view_code'],
            'implementation': ['show_source'],
            'view': ['show_source', 'view_code'],
            
            # System info
            'info': ['system_info'],
            'status': ['system_status'],
            'health': ['check_health'],
            'diagnostic': ['diagnostics'],
            'version': ['version_info'],
            
            # Modules
            'module': ['list_modules', 'module_info'],
            'package': ['list_modules', 'module_info'],
            'list': ['list_commands', 'list_modules'],
            
            # Commands
            'command': ['list_commands', 'command_help'],
            'help': ['command_help', 'show_help'],
            'usage': ['command_help'],
            
            # Documentation
            'doc': ['show_doc'],
            'documentation': ['show_doc'],
            'help': ['show_help'],
            
            # Memory
            'memory': ['memory_usage'],
            'ram': ['memory_usage'],
            'usage': ['memory_usage', 'resource_usage'],
            
            # Logs
            'log': ['show_logs'],
            'error': ['show_errors'],
            'warning': ['show_warnings'],
        }
    
    def find_command(self, query: str) -> str:
        """
        Find the most relevant command based on natural language query
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (command_name, confidence_score)
        """
        query = query.lower().strip()
        best_match = (None, 0.0)
        
        for keyword, commands in self._command_map.items():
            if keyword in query:
                for cmd in commands:
                    # Simple scoring: count matching keywords
                    score = sum(1 for word in query.split() if word in cmd)
                    if score > best_match[1]:
                        best_match = (cmd, score)
        
        return best_match[0] or 'show_help'
    
    def show_config(self, section: str = None) -> None:
        """
        Show configuration settings
        
        Args:
            section: Optional section to show (e.g., 'model', 'logging')
        """
        config = self.agent.config if hasattr(self.agent, 'config') else {}
        
        if section:
            if section in config:
                self._print_dict(config[section], title=f"Config: {section}")
            else:
                self.console.print(f"[red]No such config section: {section}[/red]")
        else:
            self._print_dict(config, title="Configuration")
    
    def show_source(self, target: str) -> None:
        """
        Show source code for a module, class, or function
        
        Args:
            target: Dot path to the target (e.g., 'ellma.core.agent.ELLMa')
        """
        try:
            parts = target.split('.')
            module_path = '.'.join(parts[:-1])
            attr_name = parts[-1]
            
            module = importlib.import_module(module_path)
            obj = getattr(module, attr_name)
            
            source = inspect.getsource(obj)
            syntax = Syntax(source, 'python', theme='monokai', line_numbers=True)
            self.console.print(Panel(syntax, title=f"Source: {target}"))
            
        except (ImportError, AttributeError, TypeError) as e:
            self.console.print(f"[red]Error showing source: {e}[/red]")
    
    def system_info(self) -> None:
        """Show detailed system information"""
        import platform
        import psutil
        
        info = {
            'System': {
                'OS': f"{platform.system()} {platform.release()}",
                'Version': platform.version(),
                'Machine': platform.machine(),
                'Processor': platform.processor(),
                'Python': platform.python_version(),
            },
            'CPU': {
                'Cores': psutil.cpu_count(logical=False),
                'Threads': psutil.cpu_count(),
                'Usage': f"{psutil.cpu_percent()}%"
            },
            'Memory': {
                'Total': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
                'Available': f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
                'Used': f"{psutil.virtual_memory().percent}%"
            },
            'Disk': {
                'Total': f"{psutil.disk_usage('/').total / (1024**3):.1f} GB",
                'Used': f"{psutil.disk_usage('/').percent}%"
            }
        }
        
        self._print_dict(info, title="System Information")
    
    def list_commands(self) -> None:
        """List all available commands"""
        if not hasattr(self.agent, 'commands'):
            self.console.print("[yellow]No commands loaded[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command")
        table.add_column("Description")
        
        for name, cmd in self.agent.commands.items():
            if hasattr(cmd, 'description'):
                desc = cmd.description.split('\n')[0]  # First line only
                table.add_row(name, desc)
        
        self.console.print(Panel(table, title="Available Commands"))
    
    def module_info(self, module_name: str = None) -> None:
        """
        Show information about a module
        
        Args:
            module_name: Name of the module to inspect
        """
        if not module_name:
            self._list_modules()
            return
            
        try:
            module = importlib.import_module(module_name)
            info = {
                'Name': module.__name__,
                'File': getattr(module, '__file__', 'Built-in'),
                'Package': getattr(module, '__package__', ''),
                'Description': inspect.getdoc(module) or 'No description',
            }
            
            self._print_dict(info, title=f"Module: {module_name}")
            
        except ImportError as e:
            self.console.print(f"[red]Error loading module: {e}[/red]")
    
    def _list_modules(self) -> None:
        """List all available Python modules"""
        import pkgutil
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Module")
        table.add_column("Description")
        
        for module in pkgutil.iter_modules():
            if module.name.startswith('ellma'):
                table.add_row(module.name, module.module_finder.path if hasattr(module, 'module_finder') else '')
        
        self.console.print(Panel(table, title="Available Modules"))
    
    def _print_dict(self, data: Dict, title: str = "") -> None:
        """Print a dictionary as a formatted table"""
        if not data:
            self.console.print("[yellow]No data to display[/yellow]")
            return
            
        table = Table(show_header=bool(title), header_style="bold blue", box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="")
        
        def add_rows(d, prefix=''):
            for k, v in d.items():
                if isinstance(v, dict):
                    table.add_row(f"{prefix}{k}:", "")
                    add_rows(v, prefix + "  ")
                else:
                    table.add_row(f"{prefix}{k}", str(v))
        
        add_rows(data)
        
        if title:
            self.console.print(Panel(table, title=title))
        else:
            self.console.print(table)
    
    def __call__(self, query: str) -> None:
        """Handle natural language queries"""
        if not query:
            self.show_help()
            return
            
        # Try to find the best matching command
        command = self.find_command(query)
        if hasattr(self, command):
            getattr(self, command)()
        else:
            self.console.print(f"[yellow]No matching command found for: {query}[/yellow]")
            self.show_help()
    
    def show_help(self) -> None:
        """Show help for introspection commands"""
        help_text = """[bold]System Introspection Commands:[/bold]

[cyan]Configuration:[/cyan]
  config [section]    - Show configuration settings
  setting [name]      - Show a specific setting

[cyan]Source Code:[/cyan]
  source <target>     - Show source code for module/class/function
  code <target>       - Alias for 'source'

[cyan]System Info:[/cyan]
  info                - Show system information
  status             - Show system status
  health             - Run system health check
  version            - Show version information

[cyan]Modules:[/cyan]
  modules             - List all available modules
  module <name>      - Show information about a module

[cyan]Commands:[/cyan]
  commands           - List all available commands
  help <command>     - Show help for a command

[cyan]Examples:[/cyan]
  sys config model
  sys source ellma.core.agent.ELLMa
  sys info
  sys modules
"""
        self.console.print(Panel(help_text, title="System Introspection Help"))
