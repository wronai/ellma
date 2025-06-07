"""
System health command.

This module provides the `health` command which performs a quick health check.
"""

from typing import Dict, Any, List
from datetime import datetime
import psutil

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn

from ..commands import BaseCommand, CommandResult
from ...core import (
    get_resource_usage,
    get_uptime,
    get_load_average
)

class HealthCommand(BaseCommand):
    """Perform a quick system health check."""
    
    def execute(self, *args, **kwargs) -> CommandResult:
        """Execute the health command.
        
        Returns:
            CommandResult: Contains the health check results.
        """
        try:
            # Get basic system information
            health_data = {}
            
            with Progress(
                SpinnerColumn(),
                "* Performing health check...",
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Checking...", total=4)
                
                # Get resource usage
                resources = get_resource_usage()
                health_data["resources"] = resources
                progress.update(task, advance=1, description="Checking resources...")
                
                # Get system load
                load_avg = get_load_average()
                if load_avg:
                    health_data["load_average"] = load_avg
                progress.update(task, advance=1, description="Checking system load...")
                
                # Get uptime
                uptime = get_uptime()
                health_data["uptime"] = uptime
                progress.update(task, advance=1, description="Checking uptime...")
                
                # Calculate health status
                health_status = self._calculate_health_status(health_data)
                health_data["status"] = health_status
                progress.update(task, advance=1, description="Finalizing...")
                
                # Display the results
                self._display_health_status(health_data)
                
                return CommandResult(success=True, data=health_data)
                
        except Exception as e:
            error_msg = f"Failed to perform health check: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _calculate_health_status(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the overall health status based on system metrics.
        
        Args:
            health_data: Dictionary containing health check data.
            
        Returns:
            Dictionary with health status information.
        """
        resources = health_data.get("resources", {})
        
        # Initialize status
        status = {
            "overall": "healthy",
            "issues": [],
            "metrics": {}
        }
        
        # Check CPU usage
        cpu_usage = resources.get("cpu_percent", 0)
        status["metrics"]["cpu_usage"] = {
            "value": cpu_usage,
            "unit": "%",
            "status": "ok"
        }
        
        if cpu_usage > 90:
            status["metrics"]["cpu_usage"]["status"] = "critical"
            status["issues"].append("CPU usage is very high")
        elif cpu_usage > 70:
            status["metrics"]["cpu_usage"]["status"] = "warning"
            status["issues"].append("CPU usage is high")
        
        # Check memory usage
        memory = resources.get("memory", {})
        memory_usage = memory.get("percent", 0)
        status["metrics"]["memory_usage"] = {
            "value": memory_usage,
            "unit": "%",
            "status": "ok"
        }
        
        if memory_usage > 95:
            status["metrics"]["memory_usage"]["status"] = "critical"
            status["issues"].append("Memory usage is very high")
        elif memory_usage > 85:
            status["metrics"]["memory_usage"]["status"] = "warning"
            status["issues"].append("Memory usage is high")
        
        # Check swap usage
        swap = resources.get("swap", {})
        swap_usage = swap.get("percent", 0)
        if swap_usage > 0:  # Only check if swap is configured
            status["metrics"]["swap_usage"] = {
                "value": swap_usage,
                "unit": "%",
                "status": "ok"
            }
            
            if swap_usage > 50:
                status["metrics"]["swap_usage"]["status"] = "warning"
                status["issues"].append("High swap usage")
        
        # Check disk usage
        for disk, usage in resources.get("disk_usage", {}).items():
            disk_usage = usage.get("percent", 0)
            status["metrics"][f"disk_usage_{disk}"] = {
                "value": disk_usage,
                "unit": "%",
                "status": "ok"
            }
            
            if disk_usage > 95:
                status["metrics"][f"disk_usage_{disk}"]["status"] = "critical"
                status["issues"].append(f"Disk {disk} is almost full")
            elif disk_usage > 85:
                status["metrics"][f"disk_usage_{disk}"]["status"] = "warning"
                status["issues"].append(f"Disk {disk} is getting full")
        
        # Check load average
        load_avg = health_data.get("load_average")
        if load_avg and len(load_avg) >= 3:
            cpu_count = psutil.cpu_count()
            load_1, load_5, load_15 = load_avg
            
            status["metrics"]["load_average"] = {
                "1min": {"value": load_1, "status": "ok"},
                "5min": {"value": load_5, "status": "ok"},
                "15min": {"value": load_15, "status": "ok"}
            }
            
            if load_1 > cpu_count * 2:
                status["metrics"]["load_average"]["1min"]["status"] = "critical"
                status["issues"].append("High system load (1min)")
            elif load_1 > cpu_count:
                status["metrics"]["load_average"]["1min"]["status"] = "warning"
                
            if load_5 > cpu_count * 2:
                status["metrics"]["load_average"]["5min"]["status"] = "critical"
                status["issues"].append("High system load (5min)")
            elif load_5 > cpu_count:
                status["metrics"]["load_average"]["5min"]["status"] = "warning"
                
            if load_15 > cpu_count * 2:
                status["metrics"]["load_average"]["15min"]["status"] = "critical"
                status["issues"].append("High system load (15min)")
            elif load_15 > cpu_count:
                status["metrics"]["load_average"]["15min"]["status"] = "warning"
        
        # Set overall status
        if any(metric.get("status") == "critical" for metric in status["metrics"].values() if isinstance(metric, dict)):
            status["overall"] = "critical"
        elif any(metric.get("status") == "warning" for metric in status["metrics"].values() if isinstance(metric, dict)):
            status["overall"] = "warning"
        
        return status
    
    def _display_health_status(self, health_data: Dict[str, Any]) -> None:
        """Display the health status in a user-friendly format.
        
        Args:
            health_data: Dictionary containing health check data.
        """
        status = health_data.get("status", {})
        overall_status = status.get("overall", "unknown")
        
        # Determine status color and emoji
        status_colors = {
            "healthy": ("green", "✓"),
            "warning": ("yellow", "!"),
            "critical": ("red", "✗"),
            "unknown": ("blue", "?")
        }
        color, emoji = status_colors.get(overall_status, ("blue", "?"))
        
        # Create status table
        status_table = Table(show_header=False, box=None)
        status_table.add_column("", style="dim", width=25)
        status_table.add_column("", style="")
        
        status_table.add_row("Overall Status", f"[{color}]{emoji} {overall_status.upper()}[/{color}]")
        status_table.add_row("Uptime", health_data.get("uptime", "N/A"))
        
        # Add load average if available
        load_avg = health_data.get("load_average")
        if load_avg:
            status_table.add_row("Load Average", ", ".join(f"{load:.2f}" for load in load_avg[:3]))
        
        # Display status table
        self.console.print(Panel(
            status_table,
            title="[bold]System Health Status[/bold]",
            border_style=color
        ))
        
        # Display metrics
        metrics = status.get("metrics", {})
        if metrics:
            metrics_table = Table(
                title="System Metrics",
                show_header=True,
                header_style="bold magenta",
                box=None
            )
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")
            metrics_table.add_column("Status", style="white")
            
            # Add CPU and Memory metrics
            if "cpu_usage" in metrics:
                cpu = metrics["cpu_usage"]
                metrics_table.add_row(
                    "CPU Usage",
                    f"{cpu['value']:.1f}%",
                    self._format_status(cpu.get("status", "unknown"))
                )
            
            if "memory_usage" in metrics:
                mem = metrics["memory_usage"]
                metrics_table.add_row(
                    "Memory Usage",
                    f"{mem['value']:.1f}%",
                    self._format_status(mem.get("status", "unknown"))
                )
            
            if "swap_usage" in metrics:
                swap = metrics["swap_usage"]
                metrics_table.add_row(
                    "Swap Usage",
                    f"{swap['value']:.1f}%",
                    self._format_status(swap.get("status", "unknown"))
                )
            
            # Add disk metrics
            for key, disk in metrics.items():
                if key.startswith("disk_usage_") and isinstance(disk, dict):
                    disk_name = key.replace("disk_usage_", "")
                    metrics_table.add_row(
                        f"Disk Usage ({disk_name})",
                        f"{disk['value']:.1f}%",
                        self._format_status(disk.get("status", "unknown"))
                    )
            
            # Add load average metrics if available
            if "load_average" in metrics:
                load = metrics["load_average"]
                metrics_table.add_row(
                    "Load Average (1/5/15 min)",
                    f"{load['1min']['value']:.2f} / {load['5min']['value']:.2f} / {load['15min']['value']:.2f}",
                    ", ".join([
                        self._format_status(load[interval].get("status", "unknown"))
                        for interval in ["1min", "5min", "15min"]
                    ])
                )
            
            self.console.print(metrics_table)
        
        # Display issues if any
        issues = status.get("issues", [])
        if issues:
            self.console.print("\n[bold]Issues:[/bold]")
            for issue in issues:
                self.console.print(f"  • [yellow]{issue}[/yellow]")
    
    def _format_status(self, status: str) -> str:
        """Format status with appropriate color.
        
        Args:
            status: Status string (ok, warning, critical, unknown).
            
        Returns:
            Formatted status string with color.
        """
        status_map = {
            "ok": "[green]OK[/green]",
            "warning": "[yellow]WARNING[/yellow]",
            "critical": "[red]CRITICAL[/red]",
            "unknown": "[blue]UNKNOWN[/blue]"
        }
        return status_map.get(status.lower(), f"[blue]{status.upper()}[/blue]")

def execute(*args, **kwargs) -> CommandResult:
    """Execute the health command.
    
    This is the entry point for the health command.
    
    Returns:
        CommandResult: The result of the command execution.
    """
    return HealthCommand().execute(*args, **kwargs)
