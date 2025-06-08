"""
Process management command.

This module provides the `processes` command which lists and manages running processes.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import psutil
import signal
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from ..commands import BaseCommand, CommandResult
from ...core import get_process_info

class ProcessesCommand(BaseCommand):
    """List and manage running processes."""
    
    def execute(self, 
               sort_by: str = "cpu", 
               limit: int = 10,
               tree: bool = False,
               full: bool = False,
               *args, **kwargs) -> CommandResult:
        """Execute the processes command.
        
        Args:
            sort_by: Field to sort by (cpu, memory, pid, name, user, time).
            limit: Maximum number of processes to display.
            tree: Display process tree instead of flat list.
            full: Show full command line arguments.
            
        Returns:
            CommandResult: Contains process information.
        """
        try:
            # Get process information
            process_data = get_process_info(detailed=True)
            processes = self._get_process_list(process_data)
            
            # Sort processes
            processes = self._sort_processes(processes, sort_by)
            
            # Limit number of processes
            if limit > 0:
                processes = processes[:limit]
            
            # Display processes
            if tree:
                self._display_process_tree(processes, full)
            else:
                self._display_process_table(processes, full)
            
            return CommandResult(success=True, data={"processes": processes})
            
        except Exception as e:
            error_msg = f"Failed to list processes: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _get_process_list(self, process_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert process data to a list of process dictionaries.
        
        Args:
            process_data: Raw process data from get_process_info.
            
        Returns:
            List of process dictionaries with detailed information.
        """
        processes = []
        
        # Get top CPU and memory processes
        top_processes = set()
        for proc in process_data.get("top_cpu", []) + process_data.get("top_memory", []):
            try:
                pid = proc.get("pid")
                if pid and pid not in top_processes:
                    top_processes.add(pid)
                    processes.append(self._get_process_details(pid))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def _get_process_details(self, pid: int) -> Dict[str, Any]:
        """Get detailed information about a process.
        
        Args:
            pid: Process ID.
            
        Returns:
            Dictionary with process details.
        """
        try:
            proc = psutil.Process(pid)
            
            # Get process info with error handling
            with proc.oneshot():
                try:
                    cpu_percent = proc.cpu_percent()
                    memory_info = proc.memory_info()
                    memory_percent = proc.memory_percent()
                    create_time = proc.create_time()
                    
                    # Calculate runtime
                    runtime = datetime.now().timestamp() - create_time
                    hours, remainder = divmod(int(runtime), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Get command line with error handling
                    try:
                        cmdline = " ".join(proc.cmdline())
                    except (psutil.AccessDenied, psutil.ZombieProcess):
                        cmdline = "[Access Denied]"
                    
                    # Get username with error handling
                    try:
                        username = proc.username()
                    except (psutil.AccessDenied, KeyError):
                        username = "N/A"
                    
                    # Get parent PID with error handling
                    try:
                        ppid = proc.ppid()
                    except (psutil.AccessDenied, psutil.ZombieProcess):
                        ppid = None
                    
                    # Get status with error handling
                    try:
                        status = proc.status()
                    except (psutil.AccessDenied, psutil.ZombieProcess):
                        status = "unknown"
                    
                    return {
                        "pid": pid,
                        "ppid": ppid,
                        "name": proc.name(),
                        "username": username,
                        "status": status,
                        "cpu_percent": cpu_percent,
                        "memory_rss": memory_info.rss,
                        "memory_vms": memory_info.vms,
                        "memory_percent": memory_percent,
                        "create_time": create_time,
                        "runtime": runtime,
                        "runtime_str": runtime_str,
                        "cmdline": cmdline,
                        "exe": proc.exe(),
                        "cwd": proc.cwd(),
                        "num_threads": proc.num_threads(),
                        "num_fds": proc.num_fds() if hasattr(proc, 'num_fds') else 0,
                        "connections": self._get_process_connections(pid)
                    }
                except (psutil.AccessDenied, psutil.ZombieProcess) as e:
                    return {
                        "pid": pid,
                        "error": str(e)
                    }
        except psutil.NoSuchProcess:
            return {
                "pid": pid,
                "error": "No such process"
            }
    
    def _get_process_connections(self, pid: int) -> List[Dict[str, Any]]:
        """Get network connections for a process.
        
        Args:
            pid: Process ID.
            
        Returns:
            List of connection dictionaries.
        """
        try:
            proc = psutil.Process(pid)
            connections = proc.connections()
            
            result = []
            for conn in connections:
                result.append({
                    "family": conn.family.name,
                    "type": conn.type.name,
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if hasattr(conn, 'raddr') and conn.raddr else "",
                    "status": conn.status
                })
            return result
        except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess):
            return []
    
    def _sort_processes(self, processes: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort processes by the specified field.
        
        Args:
            processes: List of process dictionaries.
            sort_by: Field to sort by.
            
        Returns:
            Sorted list of processes.
        """
        if not processes:
            return processes
        
        sort_key = sort_by.lower()
        reverse = True  # Default to descending order for most fields
        
        # Define sort key functions
        sort_funcs = {
            "cpu": lambda p: p.get("cpu_percent", 0),
            "memory": lambda p: p.get("memory_percent", 0),
            "pid": lambda p: p.get("pid", 0),
            "name": lambda p: p.get("name", "").lower(),
            "user": lambda p: p.get("username", "").lower(),
            "time": lambda p: p.get("runtime", 0),
            "status": lambda p: p.get("status", "").lower(),
        }
        
        # Get the appropriate sort function
        sort_func = sort_funcs.get(sort_key, sort_funcs["cpu"])
        
        # Special case for name and user (ascending)
        if sort_key in ["name", "user"]:
            reverse = False
        
        # Sort the processes
        return sorted(processes, key=sort_func, reverse=reverse)
    
    def _display_process_table(self, processes: List[Dict[str, Any]], full: bool = False) -> None:
        """Display processes in a table.
        
        Args:
            processes: List of process dictionaries.
            full: Whether to show full command line.
        """
        if not processes:
            self.console.print("[yellow]No processes found.[/yellow]")
            return
        
        table = Table(
            title="Running Processes",
            show_header=True,
            header_style="bold magenta",
            box=None
        )
        
        # Add columns
        table.add_column("PID", style="cyan")
        table.add_column("User", style="green")
        table.add_column("CPU %", justify="right")
        table.add_column("MEM %", justify="right")
        table.add_column("RSS", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Status", style="yellow")
        table.add_column("Command")
        
        # Add rows
        for proc in processes:
            if "error" in proc:
                continue
                
            # Format memory
            rss = self._format_bytes(proc.get("memory_rss", 0))
            
            # Get status with color
            status = proc.get("status", "unknown").lower()
            status_color = {
                "running": "green",
                "sleeping": "blue",
                "idle": "cyan",
                "zombie": "red",
                "stopped": "yellow",
                "tracing stop": "yellow",
                "dead": "red",
            }.get(status, "white")
            
            # Get command (full or just name)
            cmd = proc["cmdline"] if full and proc.get("cmdline") else proc["name"]
            
            table.add_row(
                str(proc["pid"]),
                proc.get("username", ""),
                f"{proc.get('cpu_percent', 0):.1f}",
                f"{proc.get('memory_percent', 0):.1f}",
                rss,
                proc.get("runtime_str", ""),
                f"[{status_color}]{status.capitalize()}[/{status_color}]",
                cmd[:100] + ("..." if len(cmd) > 100 else "")  # Truncate long commands
            )
        
        self.console.print(table)
        self.console.print(f"[dim]Showing {len(processes)} processes[/dim]")
    
    def _display_process_tree(self, processes: List[Dict[str, Any]], full: bool = False) -> None:
        """Display processes in a tree structure.
        
        Args:
            processes: List of process dictionaries.
            full: Whether to show full command line.
        """
        if not processes:
            self.console.print("[yellow]No processes found.[/yellow]")
            return
        
        # Build process tree
        process_map = {p["pid"]: p for p in processes if "error" not in p}
        children = {}
        
        # Find all children
        for pid, proc in process_map.items():
            ppid = proc.get("ppid")
            if ppid is not None:
                if ppid not in children:
                    children[ppid] = []
                children[ppid].append(pid)
        
        # Find root processes (those with no parent in our list or parent doesn't exist)
        roots = []
        for pid in process_map:
            proc = process_map[pid]
            ppid = proc.get("ppid")
            if ppid is None or ppid not in process_map:
                roots.append(pid)
        
        # If no roots found (unlikely), use all processes
        if not roots:
            roots = list(process_map.keys())
        
        # Display tree
        self.console.print("[bold]Process Tree:[/bold]")
        for root in sorted(roots):
            self._print_process_tree(root, process_map, children, "", full)
    
    def _print_process_tree(self, pid: int, 
                          process_map: Dict[int, Dict], 
                          children: Dict[int, List[int]], 
                          prefix: str,
                          full: bool) -> None:
        """Recursively print process tree.
        
        Args:
            pid: Process ID.
            process_map: Dictionary mapping PIDs to process info.
            children: Dictionary mapping parent PIDs to child PIDs.
            prefix: Prefix for indentation.
            full: Whether to show full command line.
        """
        if pid not in process_map:
            return
            
        proc = process_map[pid]
        
        # Format process info
        cpu = f"{proc.get('cpu_percent', 0):5.1f}%"
        mem = f"{proc.get('memory_percent', 0):5.1f}%"
        
        # Get command (full or just name)
        cmd = proc["cmdline"] if full and proc.get("cmdline") else proc["name"]
        
        # Print process info
        self.console.print(
            f"{prefix}├─ {pid} {cpu} {mem} {cmd}"
        )
        
        # Print children
        child_pids = children.get(pid, [])
        for i, child_pid in enumerate(sorted(child_pids)):
            is_last = i == len(child_pids) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            child_prefix = prefix + ("    " if is_last else "│   ") + "└─ "
            self._print_process_tree(child_pid, process_map, children, new_prefix, full)

def execute(sort_by: str = "cpu", limit: int = 10, tree: bool = False, full: bool = False, *args, **kwargs) -> CommandResult:
    """Execute the processes command.
    
    This is the entry point for the processes command.
    
    Args:
        sort_by: Field to sort by (cpu, memory, pid, name, user, time).
        limit: Maximum number of processes to display.
        tree: Display process tree instead of flat list.
        full: Show full command line arguments.
        
    Returns:
        CommandResult: The result of the command execution.
    """
    return ProcessesCommand().execute(sort_by=sort_by, limit=limit, tree=tree, full=full, *args, **kwargs)
