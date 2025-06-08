""
System scan command.

This module provides the `scan` command which performs a comprehensive system scan.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import time
import psutil
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..commands import BaseCommand, CommandResult
from ...core import (
    get_platform_info,
    get_hardware_info,
    get_resource_usage,
    get_network_info,
    get_storage_info,
    get_process_info,
    get_services_info,
    get_security_status,
    get_load_average,
    get_uptime
)
from ...utils import calculate_health_score

class ScanCommand(BaseCommand):
    """Perform a comprehensive system scan."""
    
    def execute(self, quick: bool = False, *args, **kwargs) -> CommandResult:
        """Execute the scan command.
        
        Args:
            quick: If True, perform a quick scan with less detail.
            
        Returns:
            CommandResult: Contains the scan results.
        """
        try:
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                "* " + ("Quick " if quick else "Full ") + "System Scan in progress",
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Scanning...", total=7)  # Number of scan steps
                
                # Gather system information
                scan_results = {}
                
                # Platform info
                scan_results["platform"] = get_platform_info()
                progress.update(task, advance=1, description="Gathering platform info...")
                
                # Hardware info
                scan_results["hardware"] = get_hardware_info()
                progress.update(task, advance=1, description="Gathering hardware info...")
                
                # Resource usage
                scan_results["resources"] = get_resource_usage()
                progress.update(task, advance=1, description="Checking resource usage...")
                
                # Network info
                scan_results["network"] = get_network_info()
                progress.update(task, advance=1, description="Checking network...")
                
                # Storage info
                scan_results["storage"] = get_storage_info()
                progress.update(task, advance=1, description="Checking storage...")
                
                # Process info (skip if quick scan)
                if not quick:
                    scan_results["processes"] = get_process_info(detailed=True)
                progress.update(task, advance=1, description="Checking processes...")
                
                # Services info (skip if quick scan)
                if not quick:
                    scan_results["services"] = get_services_info()
                progress.update(task, advance=1, description="Checking services...")
                
                # Security status (skip if quick scan)
                if not quick:
                    scan_results["security"] = get_security_status()
                progress.update(task, advance=1, description="Checking security...")
                
                # Calculate health score
                scan_results["health_score"] = calculate_health_score(scan_results)
                
                # Add timing information
                scan_results["scan_duration"] = time.time() - start_time
                scan_results["timestamp"] = datetime.now().isoformat()
                
                # Display the results
                self._display_scan_summary(scan_results)
                
                return CommandResult(success=True, data=scan_results)
                
        except Exception as e:
            error_msg = f"Failed to perform system scan: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _display_scan_summary(self, scan_results: Dict[str, Any]) -> None:
        """Display a summary of the scan results.
        
        Args:
            scan_results: Dictionary containing the scan results.
        """
        resources = scan_results.get("resources", {})
        health_score = scan_results.get("health_score", 0)
        
        # Create summary table
        table = Table(title="🔍 System Scan Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Status", style="white")

        # Health score
        health_status = "🟢 Excellent" if health_score > 90 else "🟡 Good" if health_score > 70 else "🔴 Needs attention"
        table.add_row("Health Score", f"{health_score}/100", health_status)

        # CPU
        cpu_usage = resources.get("cpu_percent", 0)
        cpu_status = "🟢" if cpu_usage < 70 else "🟡" if cpu_usage < 90 else "🔴"
        table.add_row("CPU Usage", f"{cpu_usage}%", cpu_status)

        # Memory
        memory = resources.get("memory", {})
        memory_usage = memory.get("percent", 0)
        memory_status = "🟢" if memory_usage < 70 else "🟡" if memory_usage < 90 else "🔴"
        table.add_row("Memory Usage", f"{memory_usage}%", memory_status)

        # Storage
        storage = scan_results.get("storage", {}).get("disks", {})
        if "/" in storage:
            disk_usage = storage["\"/\""]["percent"]
            disk_status = "🟢" if disk_usage < 80 else "🟡" if disk_usage < 95 else "🔴"
            table.add_row("Root Disk Usage", f"{disk_usage:.1f}%", disk_status)

        # Processes
        if "processes" in scan_results:
            process_count = scan_results["processes"].get("total_processes", 0)
            table.add_row("Running Processes", str(process_count), "")

        # Network
        network = scan_results.get("network", {})
        if "connections" in network:
            table.add_row("Network Connections", str(network["connections"]), "")

        # Uptime
        uptime = get_uptime()
        table.add_row("System Uptime", uptime, "")

        # Scan time
        scan_time = scan_results.get("scan_duration", 0)
        table.add_row("Scan Duration", f"{scan_time:.2f} seconds", "")

        self.console.print(table)
        
        # Add detailed sections
        self._display_detailed_info(scan_results)
    
    def _display_detailed_info(self, scan_results: Dict[str, Any]) -> None:
        """Display detailed information from the scan.
        
        Args:
            scan_results: Dictionary containing the scan results.
        """
        # CPU Details
        cpu_info = scan_results.get("hardware", {}).get("cpu", {})
        if cpu_info:
            cpu_table = Table(title="CPU Information", show_header=False, box=None)
            cpu_table.add_column("", style="dim", width=25)
            cpu_table.add_column("", style="")
            
            cpu_table.add_row("Physical Cores", str(cpu_info.get("cpu_count_physical", "N/A")))
            cpu_table.add_row("Logical Cores", str(cpu_info.get("cpu_count_logical", "N/A")))
            
            if "cpu_freq" in cpu_info and cpu_info["cpu_freq"]:
                freq = cpu_info["cpu_freq"]
                cpu_table.add_row("Current Frequency", f"{freq.get('current', 0):.2f} MHz")
                cpu_table.add_row("Min Frequency", f"{freq.get('min', 0):.2f} MHz")
                cpu_table.add_row("Max Frequency", f"{freq.get('max', 0):.2f} MHz")
            
            self.console.print(Panel(cpu_table, title="[bold]CPU Details[/bold]", border_style="blue"))
        
        # Memory Details
        memory = scan_results.get("resources", {}).get("memory", {})
        if memory:
            mem_table = Table(title="Memory Information", show_header=False, box=None)
            mem_table.add_column("", style="dim", width=25)
            mem_table.add_column("", style="")
            
            mem_table.add_row("Total", self._format_bytes(memory.get("total", 0)))
            mem_table.add_row("Available", self._format_bytes(memory.get("available", 0)))
            mem_table.add_row("Used", f"{self._format_bytes(memory.get('used', 0))} ({memory.get('percent', 0)}%)")
            mem_table.add_row("Free", self._format_bytes(memory.get("free", 0)))
            
            swap = scan_results.get("resources", {}).get("swap", {})
            if swap:
                mem_table.add_row("", "")
                mem_table.add_row("[bold]Swap:[/bold]", "")
                mem_table.add_row("  Total", self._format_bytes(swap.get("total", 0)))
                mem_table.add_row("  Used", f"{self._format_bytes(swap.get('used', 0))} ({swap.get('percent', 0)}%)")
                mem_table.add_row("  Free", self._format_bytes(swap.get("free", 0)))
            
            self.console.print(Panel(mem_table, title="[bold]Memory Details[/bold]", border_style="green"))
        
        # Storage Details
        storage = scan_results.get("storage", {}).get("disks", {})
        if storage:
            storage_table = Table(title="Storage Information", box=None)
            storage_table.add_column("Mount Point", style="cyan")
            storage_table.add_column("Total", style="white")
            storage_table.add_column("Used", style="white")
            storage_table.add_column("Free", style="white")
            storage_table.add_column("Use %", style="white")
            storage_table.add_column("Filesystem", style="white")
            
            for mount, info in storage.items():
                storage_table.add_row(
                    mount,
                    self._format_bytes(info.get("total", 0)),
                    self._format_bytes(info.get("used", 0)),
                    self._format_bytes(info.get("free", 0)),
                    f"{info.get('percent', 0):.1f}%",
                    info.get("fstype", "N/A")
                )
            
            self.console.print(Panel(storage_table, title="[bold]Storage Details[/bold]", border_style="yellow"))
        
        # Security Status
        security = scan_results.get("security", {})
        if security:
            sec_table = Table(title="Security Status", show_header=False, box=None)
            sec_table.add_column("", style="dim", width=25)
            sec_table.add_column("", style="")
            
            sec_table.add_row("SSH Connections", str(security.get("ssh_connections", 0)))
            sec_table.add_row("Open Ports", ", ".join(map(str, security.get("open_ports", []))) or "None")
            
            self.console.print(Panel(sec_table, title="[bold]Security Status[/bold]", border_style="red"))

def execute(quick: bool = False, *args, **kwargs) -> CommandResult:
    """Execute the scan command.
    
    This is the entry point for the scan command.
    
    Args:
        quick: If True, perform a quick scan with less detail.
        
    Returns:
        CommandResult: The result of the command execution.
    """
    return ScanCommand().execute(quick=quick, *args, **kwargs)
