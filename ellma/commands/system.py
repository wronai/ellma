"""
ELLMa System Commands - System Administration and Monitoring

This module provides system-level commands for monitoring, analysis,
and administration tasks on the local machine.
"""

import os
import sys
import subprocess
import platform
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
from rich.text import Text
from rich.panel import Panel

import psutil
from rich.console import Console
from rich.table import Table

from ellma.commands.base import BaseCommand
from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class SystemCommands(BaseCommand):
    """
    System Commands Module

    Provides comprehensive system monitoring, analysis, and administration
    capabilities for the local machine.
    """

    def __init__(self, agent):
        """Initialize System Commands"""
        super().__init__(agent)
        self.name = "system"
        self.console = Console()
        
    def config(self) -> Dict[str, Any]:
        """
        Display system and agent configuration
        
        Returns:
            Dict containing system and agent configuration
        """
        config = {
            'system': {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname(),
                'ip_address': socket.gethostbyname(socket.gethostname()),  
            },
            'resources': {
                'cpu_cores': psutil.cpu_count(),
                'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'total_disk_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            },
            'agent': {
                'name': self.agent.config.get('name', 'ELLMa'),
                'version': self.agent.config.get('version', '1.0.0'),
                'environment': self.agent.config.get('environment', 'development'),
                'log_level': self.agent.config.get('log_level', 'INFO'),
                'modules_loaded': list(self.agent.modules.keys()) if hasattr(self.agent, 'modules') else []
            }
        }
        
        # Display the configuration in a nice format
        self.console.print("\n[bold blue]System Configuration:[/bold blue]")
        sys_table = Table(show_header=False, box=None)
        sys_table.add_column("Key", style="cyan", width=20)
        sys_table.add_column("Value", style="white")
        
        for key, value in config['system'].items():
            sys_table.add_row(key.replace('_', ' ').title(), str(value))
            
        self.console.print(sys_table)
        
        self.console.print("\n[bold blue]Resource Information:[/bold blue]")
        res_table = Table(show_header=False, box=None)
        res_table.add_column("Resource", style="cyan", width=20)
        res_table.add_column("Value", style="white")
        
        for key, value in config['resources'].items():
            res_table.add_row(key.replace('_', ' ').title(), str(value) + (" GB" if key != 'cpu_cores' else " cores"))
            
        self.console.print(res_table)
        
        self.console.print("\n[bold blue]Agent Configuration:[/bold blue]")
        agent_table = Table(show_header=False, box=None)
        agent_table.add_column("Setting", style="cyan", width=20)
        agent_table.add_column("Value", style="white")
        
        for key, value in config['agent'].items():
            if isinstance(value, list):
                value = ", ".join(value) if value else "None"
            agent_table.add_row(key.replace('_', ' ').title(), str(value))
            
        self.console.print(agent_table)
        
        return config

    def scan(self, quick: bool = False) -> Dict[str, Any]:
        """
        Comprehensive system scan

        Args:
            quick: Perform quick scan (less detailed)

        Returns:
            Dict containing system information
        """
        self.console.print("[yellow]🔍 Scanning system...[/yellow]")

        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "platform": self._get_platform_info(),
            "hardware": self._get_hardware_info(),
            "resources": self._get_resource_usage(),
            "network": self._get_network_info(),
            "storage": self._get_storage_info(),
            "processes": self._get_process_info(detailed=not quick),
            "services": self._get_services_info() if not quick else {},
            "security": self._get_security_status() if not quick else {},
            "health_score": 0
        }

        # Calculate health score
        scan_results["health_score"] = self._calculate_health_score(scan_results)

        self._display_scan_summary(scan_results)
        return scan_results

    def health(self) -> Dict[str, Any]:
        """
        Quick health check

        Returns:
            Dict containing health status
        """
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": self._get_load_average(),
            "uptime": self._get_uptime(),
            "processes_count": len(psutil.pids()),
            "alerts": []
        }

        # Generate alerts
        if health_data["cpu_usage"] > 90:
            health_data["alerts"].append("HIGH CPU USAGE")
        if health_data["memory_usage"] > 90:
            health_data["alerts"].append("HIGH MEMORY USAGE")
        if health_data["disk_usage"] > 95:
            health_data["alerts"].append("LOW DISK SPACE")

        # Health status
        if health_data["alerts"]:
            health_data["status"] = "WARNING"
        elif (health_data["cpu_usage"] > 70 or
              health_data["memory_usage"] > 80 or
              health_data["disk_usage"] > 85):
            health_data["status"] = "CAUTION"
        else:
            health_data["status"] = "HEALTHY"

        return health_data

    def monitor(self, duration: int = 60, interval: int = 5) -> Dict[str, List]:
        """
        Monitor system resources over time

        Args:
            duration: Monitoring duration in seconds
            interval: Sampling interval in seconds

        Returns:
            Dict containing time series data
        """
        self.console.print(f"[yellow]📊 Monitoring system for {duration}s (interval: {interval}s)...[/yellow]")

        monitoring_data = {
            "timestamps": [],
            "cpu_usage": [],
            "memory_usage": [],
            "disk_io": [],
            "network_io": []
        }

        start_time = time.time()
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()

        while time.time() - start_time < duration:
            current_time = datetime.now().isoformat()
            monitoring_data["timestamps"].append(current_time)

            # CPU and Memory
            monitoring_data["cpu_usage"].append(psutil.cpu_percent(interval=1))
            monitoring_data["memory_usage"].append(psutil.virtual_memory().percent)

            # Disk I/O
            current_disk_io = psutil.disk_io_counters()
            if last_disk_io:
                disk_io_rate = {
                    "read_bytes_per_sec": (current_disk_io.read_bytes - last_disk_io.read_bytes) / interval,
                    "write_bytes_per_sec": (current_disk_io.write_bytes - last_disk_io.write_bytes) / interval
                }
            else:
                disk_io_rate = {"read_bytes_per_sec": 0, "write_bytes_per_sec": 0}

            monitoring_data["disk_io"].append(disk_io_rate)
            last_disk_io = current_disk_io

            # Network I/O
            current_network_io = psutil.net_io_counters()
            if last_network_io:
                network_io_rate = {
                    "bytes_sent_per_sec": (current_network_io.bytes_sent - last_network_io.bytes_sent) / interval,
                    "bytes_recv_per_sec": (current_network_io.bytes_recv - last_network_io.bytes_recv) / interval
                }
            else:
                network_io_rate = {"bytes_sent_per_sec": 0, "bytes_recv_per_sec": 0}

            monitoring_data["network_io"].append(network_io_rate)
            last_network_io = current_network_io

            # Wait for next interval
            time.sleep(interval)

        # Calculate statistics
        monitoring_data["statistics"] = {
            "avg_cpu": sum(monitoring_data["cpu_usage"]) / len(monitoring_data["cpu_usage"]),
            "max_cpu": max(monitoring_data["cpu_usage"]),
            "avg_memory": sum(monitoring_data["memory_usage"]) / len(monitoring_data["memory_usage"]),
            "max_memory": max(monitoring_data["memory_usage"])
        }

        return monitoring_data

    def processes(self, sort_by: str = "cpu", limit: int = 10) -> List[Dict]:
        """
        List running processes

        Args:
            sort_by: Sort criterion (cpu, memory, pid, name)
            limit: Number of processes to return

        Returns:
            List of process information
        """
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                process_info = proc.info
                process_info['runtime'] = datetime.now() - datetime.fromtimestamp(process_info['create_time'])
                process_info['runtime_str'] = str(process_info['runtime']).split('.')[0]  # Remove microseconds
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort processes
        if sort_by == "cpu":
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
        elif sort_by == "pid":
            processes.sort(key=lambda x: x.get('pid', 0))
        elif sort_by == "name":
            processes.sort(key=lambda x: x.get('name', ''))

        return processes[:limit]

    def ports(self, listening_only: bool = True) -> List[Dict]:
        """
        List network connections and open ports

        Args:
            listening_only: Show only listening ports

        Returns:
            List of network connections
        """
        connections = []

        for conn in psutil.net_connections(kind='inet'):
            if listening_only and conn.status != psutil.CONN_LISTEN:
                continue

            connection_info = {
                "protocol": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid
            }

            # Get process name for the connection
            if conn.pid:
                try:
                    process = psutil.Process(conn.pid)
                    connection_info["process_name"] = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    connection_info["process_name"] = "Unknown"

            connections.append(connection_info)

        return connections

    def cleanup(self, temp_files: bool = True, cache: bool = False, logs: bool = False) -> Dict[str, Any]:
        """
        System cleanup operations

        Args:
            temp_files: Clean temporary files
            cache: Clean cache files
            logs: Clean old log files

        Returns:
            Cleanup results
        """
        cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "temp_files_cleaned": 0,
            "cache_cleaned": 0,
            "logs_cleaned": 0,
            "space_freed": 0
        }

        initial_disk_usage = psutil.disk_usage('/').used

        if temp_files:
            cleanup_results["temp_files_cleaned"] = self._cleanup_temp_files()

        if cache:
            cleanup_results["cache_cleaned"] = self._cleanup_cache()

        if logs:
            cleanup_results["logs_cleaned"] = self._cleanup_logs()

        final_disk_usage = psutil.disk_usage('/').used
        cleanup_results["space_freed"] = initial_disk_usage - final_disk_usage

        return cleanup_results

    def services(self) -> List[Dict]:
        """
        List system services (Linux/macOS)

        Returns:
            List of service information
        """
        services = []

        try:
            if platform.system() == "Linux":
                # Use systemctl to list services
                result = subprocess.run(['systemctl', 'list-units', '--type=service', '--no-pager'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if line.strip() and not line.startswith('●'):
                            parts = line.split()
                            if len(parts) >= 4:
                                services.append({
                                    "name": parts[0],
                                    "load": parts[1],
                                    "active": parts[2],
                                    "sub": parts[3],
                                    "description": " ".join(parts[4:]) if len(parts) > 4 else ""
                                })

            elif platform.system() == "Darwin":  # macOS
                # Use launchctl to list services
                result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                services.append({
                                    "pid": parts[0] if parts[0] != '-' else None,
                                    "status": parts[1],
                                    "label": parts[2]
                                })

        except subprocess.SubprocessError:
            logger.warning("Failed to retrieve service information")

        return services

    # Helper methods

    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        hardware_info = {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "swap_total": psutil.swap_memory().total,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }

        return hardware_info

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_per_core": psutil.cpu_percent(interval=1, percpu=True),
            "memory": psutil.virtual_memory()._asdict(),
            "swap": psutil.swap_memory()._asdict(),
            "load_average": self._get_load_average()
        }

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        network_info = {
            "interfaces": {},
            "connections": len(psutil.net_connections()),
            "io_counters": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        }

        # Get interface information
        for interface, addresses in psutil.net_if_addrs().items():
            interface_info = []
            for addr in addresses:
                interface_info.append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            network_info["interfaces"][interface] = interface_info

        return network_info

    def _get_storage_info(self) -> Dict[str, Any]:
        """Get storage information"""
        storage_info = {
            "disks": {},
            "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        }

        # Get disk usage for all mount points
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                storage_info["disks"][partition.mountpoint] = {
                    "device": partition.device,
                    "fstype": partition.fstype,
                    "total": partition_usage.total,
                    "used": partition_usage.used,
                    "free": partition_usage.free,
                    "percent": (partition_usage.used / partition_usage.total) * 100
                }
            except PermissionError:
                continue

        return storage_info

    def _get_process_info(self, detailed: bool = True) -> Dict[str, Any]:
        """Get process information"""
        process_info = {
            "total_processes": len(psutil.pids()),
            "top_cpu": [],
            "top_memory": []
        }

        if detailed:
            # Get top processes by CPU and memory
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))

            # Sort by CPU usage
            processes_by_cpu = sorted(processes,
                                    key=lambda x: x.info.get('cpu_percent', 0),
                                    reverse=True)
            process_info["top_cpu"] = [p.info for p in processes_by_cpu[:5]]

            # Sort by memory usage
            processes_by_memory = sorted(processes,
                                       key=lambda x: x.info.get('memory_percent', 0),
                                       reverse=True)
            process_info["top_memory"] = [p.info for p in processes_by_memory[:5]]

        return process_info

    def _get_services_info(self) -> Dict[str, Any]:
        """Get services information"""
        services_info = {
            "total_services": 0,
            "active_services": 0,
            "failed_services": 0,
            "services": []
        }

        services = self.services()
        services_info["services"] = services
        services_info["total_services"] = len(services)

        # Count active and failed services (Linux)
        for service in services:
            if service.get("active") == "active":
                services_info["active_services"] += 1
            elif service.get("active") == "failed":
                services_info["failed_services"] += 1

        return services_info

    def _get_security_status(self) -> Dict[str, Any]:
        """Get basic security status"""
        security_status = {
            "firewall_enabled": False,
            "ssh_connections": 0,
            "suspicious_processes": [],
            "open_ports": []
        }

        try:
            # Check for SSH connections
            ssh_connections = [conn for conn in psutil.net_connections()
                             if conn.laddr and conn.laddr.port == 22 and conn.status == psutil.CONN_ESTABLISHED]
            security_status["ssh_connections"] = len(ssh_connections)

            # List open ports
            open_ports = [conn.laddr.port for conn in psutil.net_connections()
                         if conn.status == psutil.CONN_LISTEN and conn.laddr]
            security_status["open_ports"] = sorted(set(open_ports))

        except Exception as e:
            logger.warning(f"Failed to get security status: {e}")

        return security_status

    def _get_load_average(self) -> Optional[List[float]]:
        """Get system load average"""
        try:
            if hasattr(os, 'getloadavg'):
                return list(os.getloadavg())
        except (OSError, AttributeError):
            pass
        return None

    def _get_uptime(self) -> str:
        """Get system uptime"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return str(uptime).split('.')[0]  # Remove microseconds

    def _calculate_health_score(self, scan_results: Dict) -> int:
        """Calculate overall system health score (0-100)"""
        score = 100

        resources = scan_results.get("resources", {})

        # CPU usage penalty
        cpu_usage = resources.get("cpu_percent", 0)
        if cpu_usage > 90:
            score -= 30
        elif cpu_usage > 70:
            score -= 15
        elif cpu_usage > 50:
            score -= 5

        # Memory usage penalty
        memory_usage = resources.get("memory", {}).get("percent", 0)
        if memory_usage > 95:
            score -= 25
        elif memory_usage > 85:
            score -= 15
        elif memory_usage > 70:
            score -= 5

        # Disk usage penalty
        storage = scan_results.get("storage", {}).get("disks", {})
        for disk_info in storage.values():
            disk_usage = disk_info.get("percent", 0)
            if disk_usage > 95:
                score -= 20
            elif disk_usage > 85:
                score -= 10
            elif disk_usage > 75:
                score -= 3

        # Security considerations
        security = scan_results.get("security", {})
        open_ports_count = len(security.get("open_ports", []))
        if open_ports_count > 20:
            score -= 10
        elif open_ports_count > 10:
            score -= 5

        return max(0, score)

    def _cleanup_temp_files(self) -> int:
        """Clean temporary files"""
        cleaned_count = 0
        temp_dirs = ["/tmp", "/var/tmp", os.path.expanduser("~/tmp")]

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                # Only remove files older than 7 days
                                if os.path.getmtime(file_path) < time.time() - 7 * 24 * 3600:
                                    os.remove(file_path)
                                    cleaned_count += 1
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue

        return cleaned_count

    def _cleanup_cache(self) -> int:
        """Clean cache files"""
        # This is a simplified implementation
        # In practice, you'd want to be more careful about which cache files to remove
        return 0

    def _cleanup_logs(self) -> int:
        """Clean old log files"""
        cleaned_count = 0
        log_dirs = ["/var/log", os.path.expanduser("~/.local/share/logs")]

        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                try:
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            if file.endswith(('.log', '.log.gz', '.log.1', '.log.2')):
                                file_path = os.path.join(root, file)
                                try:
                                    # Remove log files older than 30 days
                                    if os.path.getmtime(file_path) < time.time() - 30 * 24 * 3600:
                                        os.remove(file_path)
                                        cleaned_count += 1
                                except (OSError, PermissionError):
                                    continue
                except (OSError, PermissionError):
                    continue

        return cleaned_count
        
    def _parse_log_line(self, line: str) -> Optional[Tuple[datetime, str, str, str]]:
        """Parse a log line into timestamp, level, logger, and message."""
        # Example log format: 2023-11-15 12:34:56,789 - module.name - LEVEL - Message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^ ]+) - ([A-Z]+) - (.+)'
        match = re.match(pattern, line)
        if not match:
            return None
            
        timestamp_str, logger_name, level, message = match.groups()
        try:
            # Convert timestamp string to datetime object
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            return timestamp, level, logger_name, message
        except ValueError:
            return None
    
    def _get_log_files(self, log_type: str = 'system') -> List[Path]:
        """Get log files for the specified log type."""
        log_dir = Path.home() / ".ellma" / "logs"
        if log_type == 'system':
            return sorted(log_dir.glob('system.log*'))
        elif log_type == 'chat':
            return sorted(log_dir.glob('chat.log*'))
        return []
    
    def _read_logs(self, log_type: str = 'system', since: timedelta = None) -> List[str]:
        """Read logs of specified type, optionally filtered by time."""
        log_files = self._get_log_files(log_type)
        if not log_files:
            return []
            
        cutoff_time = datetime.now(timezone.utc) - since if since else None
        all_entries = []
        
        for log_file in reversed(log_files):  # Start from most recent logs first
            try:
                # Handle compressed logs
                if log_file.suffix == '.gz':
                    import gzip
                    with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                        lines = f.readlines()
                else:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                
                # Process lines in reverse order (newest first)
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                        
                    parsed = self._parse_log_line(line)
                    if not parsed:
                        all_entries.append((None, line))
                        continue
                        
                    timestamp, level, logger_name, message = parsed
                    if cutoff_time and timestamp < cutoff_time:
                        return all_entries  # Stop if we've gone past the cutoff
                        
                    all_entries.append((timestamp, f"{timestamp} - {logger_name} - {level} - {message}"))
                    
            except Exception as e:
                logger.warning(f"Error reading log file {log_file}: {e}")
                
        return [entry[1] for entry in all_entries if entry[1]]
    
    def logs(self, log_type: str = 'system', hours: int = 1, tail: int = 50, level: str = None) -> None:
        """
        Display recent log entries
        
        Args:
            log_type: Type of logs to display ('system' or 'chat')
            hours: Number of hours of logs to show (0 for all)
            tail: Number of most recent lines to show (0 for all)
            level: Minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if log_type not in ['system', 'chat']:
            self.console.print("[red]Error:[/red] log_type must be 'system' or 'chat'")
            return
            
        since = timedelta(hours=hours) if hours > 0 else None
        log_entries = self._read_logs(log_type, since)
        
        # Apply level filter if specified
        if level and level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            min_level = getattr(logging, level.upper())
            log_entries = [
                entry for entry in log_entries
                if self._get_log_level(entry) >= min_level
            ]
        
        # Apply tail filter
        if tail > 0:
            log_entries = log_entries[-tail:]
        
        # Display logs in a table
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("Logger", style="blue", width=30)
        table.add_column("Level", style="green", width=10)
        table.add_column("Message", style="")
        
        for entry in log_entries:
            parsed = self._parse_log_line(entry)
            if parsed:
                timestamp, level, logger_name, message = parsed
                level_style = self._get_level_style(level)
                table.add_row(
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    logger_name,
                    f"[{level_style}]{level}[/{level_style}]",
                    message
                )
            else:
                table.add_row("", "", "", entry)
        
        self.console.print(Panel.fit(
            table if log_entries else "No log entries found",
            title=f"{log_type.capitalize()} Logs",
            border_style="blue"
        ))
    
    def _get_level_style(self, level: str) -> str:
        """Get rich style for log level."""
        styles = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold red'
        }
        return styles.get(level, '')
    
    def _get_log_level(self, log_entry: str) -> int:
        """Get numeric log level from log entry."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        for level_name, level_num in level_map.items():
            if f" - {level_name} - " in log_entry:
                return level_num
        return logging.DEBUG  # Default to DEBUG if level not found

    def _display_scan_summary(self, scan_results: Dict):
        """Display scan results summary"""
        resources = scan_results.get("resources", {})
        health_score = scan_results.get("health_score", 0)

        # Create summary table
        table = Table(title="🔍 System Scan Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Status", style="white")

        # Health score
        health_status = "🟢 Excellent" if health_score > 90 else "🟡 Good" if health_score > 70 else "🔴 Poor"
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
            disk_usage = storage["/"]["percent"]
            disk_status = "🟢" if disk_usage < 80 else "🟡" if disk_usage < 95 else "🔴"
            table.add_row("Disk Usage", f"{disk_usage:.1f}%", disk_status)

        # Processes
        process_count = scan_results.get("processes", {}).get("total_processes", 0)
        table.add_row("Processes", str(process_count), "")

        # Uptime
        uptime = self._get_uptime()
        table.add_row("Uptime", uptime, "")

        self.console.print(table)