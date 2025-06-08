"""
System services command.

This module provides the `services` command which manages system services.
"""

import os
import re
import subprocess
import platform
import shlex
import socket
import time
from typing import Dict, Any, List, Optional, Tuple, Union

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from ..commands import BaseCommand, CommandResult
from ...utils import get_services_info

class ServicesCommand(BaseCommand):
    """Manage system services."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_manager = self._detect_service_manager()
    
    def _detect_service_manager(self) -> str:
        """Detect the system service manager.
        
        Returns:
            Name of the service manager ('systemd', 'launchd', 'service', 'sc', 'unknown').
        """
        system = platform.system().lower()
        
        if system == 'linux':
            # Check for systemd
            if os.path.exists('/run/systemd/system'):
                return 'systemd'
            # Check for SysV init
            elif os.path.exists('/etc/init.d'):
                return 'service'
            # Check for openrc
            elif os.path.exists('/etc/init.d/rc'):
                return 'openrc'
            # Check for upstart
            elif os.path.exists('/sbin/upstart-udev-bridge'):
                return 'upstart'
            else:
                return 'unknown'
        elif system == 'darwin':  # macOS
            return 'launchd'
        elif system == 'windows':
            return 'sc'
        else:
            return 'unknown'
    
    def execute(self, 
               list_all: bool = False,
               status: Optional[str] = None,
               start: Optional[str] = None,
               stop: Optional[str] = None,
               restart: Optional[str] = None,
               enable: Optional[str] = None,
               disable: Optional[str] = None,
               show_logs: Optional[str] = None,
               follow_logs: bool = False,
               *args, **kwargs) -> CommandResult:
        """Execute the services command.
        
        Args:
            list_all: List all services.
            status: Show status of a specific service.
            start: Start a service.
            stop: Stop a service.
            restart: Restart a service.
            enable: Enable a service to start on boot.
            disable: Disable a service from starting on boot.
            show_logs: Show logs for a service.
            follow_logs: Follow log output (only with --show-logs).
            
        Returns:
            CommandResult: Contains service information or operation result.
        """
        try:
            # If no action specified, default to listing all services
            if not any([list_all, status, start, stop, restart, enable, disable, show_logs]):
                list_all = True
            
            # Execute the requested action
            if list_all:
                return self._list_services()
            elif status:
                return self._service_status(status)
            elif start:
                return self._service_action(start, 'start')
            elif stop:
                return self._service_action(stop, 'stop')
            elif restart:
                return self._service_action(restart, 'restart')
            elif enable:
                return self._service_action(enable, 'enable')
            elif disable:
                return self._service_action(disable, 'disable')
            elif show_logs:
                return self._show_logs(show_logs, follow=follow_logs)
            else:
                return CommandResult(success=False, error="No valid action specified")
                
        except Exception as e:
            error_msg = f"Failed to manage services: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _list_services(self) -> CommandResult:
        """List all system services.
        
        Returns:
            CommandResult: Contains list of services.
        """
        try:
            services = get_services_info()
            
            if not services:
                self.console.print("[yellow]No services found.[/yellow]")
                return CommandResult(success=True, data={"services": []})
            
            # Create table
            table = Table(
                title="System Services",
                show_header=True,
                header_style="bold magenta",
                box=None
            )
            
            # Add columns
            table.add_column("Name", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Description")
            table.add_column("PID", justify="right")
            table.add_column("Memory", justify="right")
            table.add_column("CPU %", justify="right")
            
            # Add rows
            for service in services:
                # Format status with color
                status = service.get('status', 'unknown').lower()
                status_color = {
                    'running': 'green',
                    'active': 'green',
                    'inactive': 'red',
                    'failed': 'red',
                    'dead': 'red',
                    'exited': 'yellow',
                }.get(status, 'white')
                
                # Format memory
                memory = service.get('memory', 0)
                memory_str = f"{memory / 1024 / 1024:.1f} MB" if memory > 0 else "N/A"
                
                # Add row
                table.add_row(
                    service.get('name', 'N/A'),
                    f"[{status_color}]{status.upper()}[/{status_color}]",
                    service.get('description', '')[:50] + ('...' if len(service.get('description', '')) > 50 else ''),
                    str(service.get('pid', 'N/A')),
                    memory_str,
                    f"{service.get('cpu_percent', 0):.1f}%" if service.get('cpu_percent') is not None else "N/A"
                )
            
            self.console.print(table)
            return CommandResult(success=True, data={"services": services, "count": len(services)})
            
        except Exception as e:
            error_msg = f"Failed to list services: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _service_status(self, service_name: str) -> CommandResult:
        """Get detailed status of a service.
        
        Args:
            service_name: Name of the service.
            
        Returns:
            CommandResult: Contains detailed service status.
        """
        try:
            # Get service info
            services = get_services_info()
            service = next((s for s in services if s.get('name') == service_name), None)
            
            if not service:
                return CommandResult(success=False, error=f"Service '{service_name}' not found")
            
            # Create status panel
            status = service.get('status', 'unknown').lower()
            status_color = 'green' if status in ['running', 'active'] else 'red' if status in ['failed', 'dead'] else 'yellow'
            
            # Get additional details based on service manager
            details = self._get_service_details(service_name)
            
            # Create info panel
            info_panel = Panel(
                f"[bold]Description:[/bold] {service.get('description', 'N/A')}\n"
                f"[bold]Status:[/bold] [{status_color}]{status.upper()}[/{status_color}]\n"
                f"[bold]PID:[/bold] {service.get('pid', 'N/A')}\n"
                f"[bold]Memory:[/bold] {service.get('memory', 0) / 1024 / 1024:.1f} MB\n"
                f"[bold]CPU %:[/bold] {service.get('cpu_percent', 0):.1f}%\n"
                f"[bold]User:[/bold] {service.get('user', 'N/A')}\n"
                f"[bold]Group:[/bold] {service.get('group', 'N/A')}\n"
                f"[bold]Start Time:[/bold] {service.get('start_time', 'N/A')}\n"
                f"[bold]Command:[/bold] {service.get('cmd', 'N/A')}",
                title=f"Service: {service_name}",
                border_style="blue"
            )
            
            self.console.print(info_panel)
            
            # Show additional details if available
            if details:
                details_panel = Panel(
                    "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in details.items() if v),
                    title="Additional Details",
                    border_style="blue"
                )
                self.console.print(details_panel)
            
            return CommandResult(success=True, data={"service": service, "details": details})
            
        except Exception as e:
            error_msg = f"Failed to get status for service '{service_name}': {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _service_action(self, service_name: str, action: str) -> CommandResult:
        """Perform an action on a service (start, stop, restart, enable, disable).
        
        Args:
            service_name: Name of the service.
            action: Action to perform (start, stop, restart, enable, disable).
            
        Returns:
            CommandResult: Result of the action.
        """
        try:
            # Check if service exists
            services = get_services_info()
            service = next((s for s in services if s.get('name') == service_name), None)
            
            if not service:
                return CommandResult(success=False, error=f"Service '{service_name}' not found")
            
            # Check if action is valid
            if action not in ['start', 'stop', 'restart', 'enable', 'disable']:
                return CommandResult(success=False, error=f"Invalid action: {action}")
            
            # Check if root/sudo is needed
            if os.geteuid() != 0:
                self.console.print("[yellow]Warning:[/yellow] This action may require root/sudo privileges.")
                if not Confirm.ask(f"Continue as non-root user?"):
                    return CommandResult(success=False, error="Operation cancelled by user")
            
            # Execute the action
            success, output = self._execute_service_action(service_name, action)
            
            if success:
                self.console.print(f"[green]✓ Successfully {action}ed service '{service_name}'[/green]")
                if output:
                    self.console.print(f"[dim]{output}[/dim]")
                
                # Show new status
                if action in ['start', 'stop', 'restart']:
                    time.sleep(1)  # Give the service a moment to update
                    return self._service_status(service_name)
                
                return CommandResult(success=True, data={"service": service_name, "action": action, "output": output})
            else:
                error_msg = f"Failed to {action} service '{service_name}'"
                if output:
                    error_msg += f": {output}"
                self.console.print(f"[red]Error:[/red] {error_msg}")
                return CommandResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Failed to {action} service '{service_name}': {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _show_logs(self, service_name: str, follow: bool = False) -> CommandResult:
        """Show logs for a service.
        
        Args:
            service_name: Name of the service.
            follow: Whether to follow the log output.
            
        Returns:
            CommandResult: Result of the log retrieval.
        """
        try:
            # Check if service exists
            services = get_services_info()
            service = next((s for s in services if s.get('name') == service_name), None)
            
            if not service:
                return CommandResult(success=False, error=f"Service '{service_name}' not found")
            
            # Get log command based on platform
            log_cmd = self._get_log_command(service_name, follow)
            
            if not log_cmd:
                return CommandResult(success=False, error=f"Log retrieval not supported for this service manager: {self.service_manager}")
            
            self.console.print(f"[bold]Showing logs for service:[/bold] {service_name}")
            self.console.print("-" * 50)
            
            # Execute log command
            try:
                if follow:
                    # Follow logs in real-time
                    process = subprocess.Popen(
                        log_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    
                    try:
                        for line in iter(process.stdout.readline, ''):
                            self.console.print(line.rstrip())
                    except KeyboardInterrupt:
                        self.console.print("\n[yellow]Stopping log follow...[/yellow]")
                        process.terminate()
                else:
                    # Show recent logs
                    result = subprocess.run(
                        log_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    if result.returncode == 0:
                        self.console.print(result.stdout)
                    else:
                        self.console.print(f"[red]Error:[/red] {result.stderr}")
                        return CommandResult(success=False, error=result.stderr)
                
                return CommandResult(success=True)
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to retrieve logs: {str(e)}"
                self.console.print(f"[red]Error:[/red] {error_msg}")
                return CommandResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Failed to show logs for service '{service_name}': {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _get_service_details(self, service_name: str) -> Dict[str, str]:
        """Get additional details about a service.
        
        Args:
            service_name: Name of the service.
            
        Returns:
            Dictionary containing additional service details.
        """
        details = {}
        
        try:
            if self.service_manager == 'systemd':
                # Get systemd service details
                cmd = f'systemctl show {shlex.quote(service_name)}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if '=' in line:
                            key, value = line.split('=', 1)
                            details[key] = value
            
            elif self.service_manager == 'launchd':  # macOS
                # Get launchd service details
                cmd = f'launchctl list {shlex.quote(service_name)}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                if result.returncode == 0:
                    details['launchd_info'] = result.stdout.strip()
            
            # Add more service managers as needed
            
        except Exception:
            # Ignore errors when getting additional details
            pass
        
        return details
    
    def _execute_service_action(self, service_name: str, action: str) -> Tuple[bool, str]:
        """Execute a service action using the appropriate service manager.
        
        Args:
            service_name: Name of the service.
            action: Action to perform (start, stop, restart, enable, disable).
            
        Returns:
            Tuple of (success, output).
        """
        try:
            cmd = ''
            
            if self.service_manager == 'systemd':
                if action in ['start', 'stop', 'restart', 'enable', 'disable']:
                    cmd = f'systemctl {action} {shlex.quote(service_name)}'
            
            elif self.service_manager == 'launchd':  # macOS
                if action == 'start':
                    cmd = f'launchctl start {shlex.quote(service_name)}'
                elif action == 'stop':
                    cmd = f'launchctl stop {shlex.quote(service_name)}'
                elif action == 'restart':
                    cmd = f'launchctl stop {shlex.quote(service_name)} && launchctl start {shlex.quote(service_name)}'
                elif action == 'enable':
                    cmd = f'launchctl load -w /System/Library/LaunchDaemons/{shlex.quote(service_name)}.plist 2>/dev/null || launchctl load -w /Library/LaunchDaemons/{shlex.quote(service_name)}.plist 2>/dev/null || launchctl load -w ~/Library/LaunchAgents/{shlex.quote(service_name)}.plist'
                elif action == 'disable':
                    cmd = f'launchctl unload -w /System/Library/LaunchDaemons/{shlex.quote(service_name)}.plist 2>/dev/null || launchctl unload -w /Library/LaunchDaemons/{shlex.quote(service_name)}.plist 2>/dev/null || launchctl unload -w ~/Library/LaunchAgents/{shlex.quote(service_name)}.plist'
            
            elif self.service_manager == 'service':  # SysV init
                if action in ['start', 'stop', 'restart']:
                    cmd = f'service {shlex.quote(service_name)} {action}'
                elif action == 'enable':
                    cmd = f'update-rc.d {shlex.quote(service_name)} enable'
                elif action == 'disable':
                    cmd = f'update-rc.d {shlex.quote(service_name)} disable'
            
            elif self.service_manager == 'sc':  # Windows
                if action in ['start', 'stop']:
                    cmd = f'net {action} {shlex.quote(service_name)}'
                elif action == 'restart':
                    cmd = f'net stop {shlex.quote(service_name)} && net start {shlex.quote(service_name)}'
                elif action == 'enable':
                    cmd = f'sc config {shlex.quote(service_name)} start= auto'
                elif action == 'disable':
                    cmd = f'sc config {shlex.quote(service_name)} start= disabled'
            
            if not cmd:
                return False, f"Action '{action}' not supported for service manager: {self.service_manager}"
            
            # Execute the command
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            output = result.stdout.strip()
            
            if result.returncode != 0:
                return False, output or f"Failed to {action} service"
            
            return True, output
            
        except Exception as e:
            return False, str(e)
    
    def _get_log_command(self, service_name: str, follow: bool = False) -> Optional[str]:
        """Get the command to show logs for a service.
        
        Args:
            service_name: Name of the service.
            follow: Whether to follow the log output.
            
        Returns:
            Command string or None if not supported.
        """
        try:
            if self.service_manager == 'systemd':
                return f'journalctl -u {shlex.quote(service_name)} ' + ('-f' if follow else '--no-pager -n 100')
            
            elif self.service_manager == 'launchd':  # macOS
                # Try to find the log file for the service
                log_paths = [
                    f'/var/log/{service_name}.log',
                    f'/var/log/system.log',
                    f'~/Library/Logs/{service_name}.log'
                ]
                
                for log_path in log_paths:
                    log_path = os.path.expanduser(log_path)
                    if os.path.exists(log_path):
                        return f'tail ' + ('-f' if follow else '-n 100') + f' {shlex.quote(log_path)}'
                
                # If no log file found, try to get logs from system log
                return f'log show --predicate "processImagePath contains \'{service_name}\'" --last 1h' + (' --style syslog --follow' if follow else '')
            
            elif self.service_manager == 'service':  # SysV init
                log_paths = [
                    f'/var/log/{service_name}.log',
                    f'/var/log/{service_name}',
                    f'/var/log/syslog',
                    f'/var/log/messages'
                ]
                
                for log_path in log_paths:
                    if os.path.exists(log_path):
                        return f'tail ' + ('-f' if follow else '-n 100') + f' {shlex.quote(log_path)} | grep -i {shlex.quote(service_name)}'
            
            elif self.service_manager == 'sc':  # Windows
                return f'Get-EventLog -LogName Application -Source {shlex.quote(service_name)} -Newest 100 | Format-Table TimeGenerated, Message -AutoSize -Wrap'
            
            return None
            
        except Exception:
            return None

def execute(list_all: bool = False, status: Optional[str] = None, 
           start: Optional[str] = None, stop: Optional[str] = None, 
           restart: Optional[str] = None, enable: Optional[str] = None, 
           disable: Optional[str] = None, show_logs: Optional[str] = None, 
           follow_logs: bool = False, *args, **kwargs) -> CommandResult:
    """Execute the services command.
    
    This is the entry point for the services command.
    
    Args:
        list_all: List all services.
        status: Show status of a specific service.
        start: Start a service.
        stop: Stop a service.
        restart: Restart a service.
        enable: Enable a service to start on boot.
        disable: Disable a service from starting on boot.
        show_logs: Show logs for a service.
        follow_logs: Follow log output (only with --show-logs).
        
    Returns:
        CommandResult: The result of the command execution.
    """
    return ServicesCommand().execute(
        list_all=list_all,
        status=status,
        start=start,
        stop=stop,
        restart=restart,
        enable=enable,
        disable=disable,
        show_logs=show_logs,
        follow_logs=follow_logs,
        *args,
        **kwargs
    )
