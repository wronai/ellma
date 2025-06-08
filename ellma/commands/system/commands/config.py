""
System configuration command.

This module provides the `config` command which displays system and agent configuration.
"""

from typing import Dict, Any, Optional
from ..commands import BaseCommand, CommandResult
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

class ConfigCommand(BaseCommand):
    """Display system and agent configuration."""
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """Execute the config command.
        
        Returns:
            CommandResult: Contains system and agent configuration.
        """
        try:
            # Get system information
            platform_info = self._get_platform_info()
            hardware_info = self._get_hardware_info()
            
            # Format the output
            config_data = {
                "system": platform_info,
                "hardware": hardware_info,
                "agent": self._get_agent_info()
            }
            
            # Display the configuration
            self._display_config(config_data)
            
            return CommandResult(success=True, data=config_data)
            
        except Exception as e:
            error_msg = f"Failed to retrieve configuration: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform information.
        
        Returns:
            Dictionary containing platform information.
        """
        import platform
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information.
        
        Returns:
            Dictionary containing hardware information.
        """
        import psutil
        import socket
        
        # Get CPU info
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        }
        
        # Add CPU frequency if available
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_info.update({
                    "max_frequency": f"{cpu_freq.max:.2f}Mhz",
                    "min_frequency": f"{cpu_freq.min:.2f}Mhz",
                    "current_frequency": f"{cpu_freq.current:.2f}Mhz"
                })
        except Exception:
            pass
        
        # Get memory info
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        hardware_info = {
            "cpu": cpu_info,
            "memory": {
                "total": self._format_bytes(svmem.total),
                "available": self._format_bytes(svmem.available),
                "used": self._format_bytes(svmem.used),
                "percent": f"{svmem.percent}%",
                "swap_total": self._format_bytes(swap.total),
                "swap_used": self._format_bytes(swap.used),
                "swap_free": self._format_bytes(swap.free),
                "swap_percent": f"{swap.percent}%"
            },
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname())
        }
        
        return hardware_info
    
    def _get_agent_info(self) -> Dict[str, Any]:
        """Get agent information.
        
        Returns:
            Dictionary containing agent information.
        """
        # This would be replaced with actual agent information
        return {
            "version": "1.0.0",
            "status": "running",
            "startup_time": "2023-11-15T12:00:00Z",
            "config_file": "~/.ellma/config.yaml"
        }
    
    def _display_config(self, config_data: Dict[str, Any]) -> None:
        """Display the configuration in a formatted way.
        
        Args:
            config_data: Dictionary containing configuration data.
        """
        # System Information
        self.console.print(Panel.fit(
            "[bold]System Information[/bold]\n" +
            "\n".join(f"[cyan]{k}:[/cyan] {v}" for k, v in config_data["system"].items()),
            title="System",
            border_style="blue"
        ))
        
        # Hardware Information
        hardware = config_data["hardware"]
        
        # CPU Info
        cpu_table = Table(show_header=False, box=None)
        cpu_table.add_column("", style="dim", width=20)
        cpu_table.add_column("", style="")
        
        cpu_info = hardware["cpu"]
        cpu_table.add_row("Physical Cores", str(cpu_info["physical_cores"]))
        cpu_table.add_row("Logical Cores", str(cpu_info["logical_cores"]))
        
        if "current_frequency" in cpu_info:
            cpu_table.add_row("Current Frequency", cpu_info["current_frequency"])
            cpu_table.add_row("Min Frequency", cpu_info["min_frequency"])
            cpu_table.add_row("Max Frequency", cpu_info["max_frequency"])
        
        # Memory Info
        memory = hardware["memory"]
        memory_table = Table(show_header=False, box=None)
        memory_table.add_column("", style="dim", width=20)
        memory_table.add_column("", style="")
        
        memory_table.add_row("Total", memory["total"])
        memory_table.add_row("Available", memory["available"])
        memory_table.add_row("Used", f"{memory['used']} ({memory['percent']})")
        memory_table.add_row("", "")
        memory_table.add_row("Swap Total", memory["swap_total"])
        memory_table.add_row("Swap Used", f"{memory['swap_used']} ({memory['swap_percent']})")
        
        # Combine hardware info
        hardware_panel = Table.grid(expand=True)
        hardware_panel.add_column("CPU")
        hardware_panel.add_column("Memory")
        hardware_panel.add_row(cpu_table, memory_table)
        
        self.console.print(Panel.fit(
            hardware_panel,
            title="Hardware",
            border_style="green"
        ))
        
        # Network Info
        network_table = Table(show_header=False, box=None)
        network_table.add_column("", style="dim", width=20)
        network_table.add_column("", style="")
        
        network_table.add_row("Hostname", hardware["hostname"])
        network_table.add_row("IP Address", hardware["ip_address"])
        
        self.console.print(Panel.fit(
            network_table,
            title="Network",
            border_style="yellow"
        ))
        
        # Agent Info
        agent_table = Table(show_header=False, box=None)
        agent_table.add_column("", style="dim", width=20)
        agent_table.add_column("", style="")
        
        agent_info = config_data["agent"]
        for key, value in agent_info.items():
            agent_table.add_row(key.replace('_', ' ').title(), str(value))
        
        self.console.print(Panel.fit(
            agent_table,
            title="Agent",
            border_style="magenta"
        ))

def execute(*args, **kwargs) -> CommandResult:
    """Execute the config command.
    
    This is the entry point for the config command.
    
    Returns:
        CommandResult: The result of the command execution.
    """
    return ConfigCommand().execute(*args, **kwargs)
