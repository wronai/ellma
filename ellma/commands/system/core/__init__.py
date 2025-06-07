"""
Core system information modules.

This package contains core functionality for retrieving system information
such as platform details, hardware information, resource usage, etc.
"""

from typing import Dict, Any, Optional, List, Tuple
import platform
import psutil
import socket
from datetime import datetime

from ..models import SystemInfo, ProcessInfo, NetworkConnection, ServiceInfo

def get_platform_info() -> Dict[str, str]:
    """
    Get platform information.

    Returns:
        Dictionary containing platform information.
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname())
    }

def get_hardware_info() -> Dict[str, Any]:
    """
    Get hardware information.

    Returns:
        Dictionary containing hardware information.
    """
    cpu_freq = psutil.cpu_freq()
    return {
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_freq": cpu_freq._asdict() if cpu_freq else {},
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "swap_total": psutil.swap_memory().total,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }

def get_resource_usage() -> Dict[str, Any]:
    """
    Get current resource usage.

    Returns:
        Dictionary containing resource usage information.
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_per_core": psutil.cpu_percent(interval=1, percpu=True),
        "memory": psutil.virtual_memory()._asdict(),
        "swap": psutil.swap_memory()._asdict(),
        "load_average": get_load_average()
    }

def get_network_info() -> Dict[str, Any]:
    """
    Get network information.

    Returns:
        Dictionary containing network information.
    """
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

def get_storage_info() -> Dict[str, Any]:
    """
    Get storage information.

    Returns:
        Dictionary containing storage information.
    """
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
                "percent": (partition_usage.used / partition_usage.total) * 100 if partition_usage.total > 0 else 0
            }
        except (PermissionError, OSError):
            continue

    return storage_info

def get_process_info(detailed: bool = True) -> Dict[str, Any]:
    """
    Get process information.

    Args:
        detailed: Whether to include detailed process information.

    Returns:
        Dictionary containing process information.
    """
    process_info = {
        "total_processes": len(psutil.pids()),
        "top_cpu": [],
        "top_memory": []
    }

    if detailed:
        # Get top processes by CPU and memory
        processes = list(psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']))

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

def get_services_info() -> Dict[str, Any]:
    """
    Get services information.

    Returns:
        Dictionary containing services information.
    """
    import subprocess
    from ..models import ServiceInfo
    
    services = []
    
    try:
        if platform.system() == "Linux":
            # Use systemctl to list services
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service', '--no-pager'],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip() and not line.startswith('●'):
                    parts = line.split()
                    if len(parts) >= 4:
                        services.append(ServiceInfo(
                            name=parts[0],
                            load=parts[1],
                            active=parts[2],
                            sub=parts[3],
                            description=" ".join(parts[4:]) if len(parts) > 4 else ""
                        ))

        elif platform.system() == "Darwin":  # macOS
            # Use launchctl to list services
            result = subprocess.run(
                ['launchctl', 'list'],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        services.append(ServiceInfo(
                            name=parts[2],
                            load=parts[0] if parts[0] != '-' else "-",
                            active=parts[1],
                            sub="",
                            description=parts[2]
                        ))

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        import logging
        logging.warning(f"Failed to retrieve service information: {e}")

    return {
        "total_services": len(services),
        "active_services": sum(1 for s in services if getattr(s, 'active', '') == 'active'),
        "failed_services": sum(1 for s in services if getattr(s, 'active', '') == 'failed'),
        "services": [s.__dict__ for s in services]
    }

def get_security_status() -> Dict[str, Any]:
    """
    Get basic security status.

    Returns:
        Dictionary containing security status information.
    """
    security_status = {
        "firewall_enabled": False,
        "ssh_connections": 0,
        "suspicious_processes": [],
        "open_ports": []
    }

    try:
        # Check for SSH connections
        ssh_connections = [
            conn for conn in psutil.net_connections()
            if conn.laddr and conn.laddr.port == 22 and conn.status == 'ESTABLISHED'
        ]
        security_status["ssh_connections"] = len(ssh_connections)

        # List open ports
        open_ports = [
            conn.laddr.port 
            for conn in psutil.net_connections()
            if conn.status == 'LISTEN' and conn.laddr
        ]
        security_status["open_ports"] = sorted(set(open_ports))

    except Exception as e:
        import logging
        logging.warning(f"Failed to get security status: {e}")

    return security_status

def get_load_average() -> Optional[List[float]]:
    """
    Get system load average.

    Returns:
        List containing load average for 1, 5, and 15 minutes, or None if not available.
    """
    try:
        if hasattr(os, 'getloadavg'):
            return list(os.getloadavg())
    except (OSError, AttributeError):
        pass
    return None

def get_uptime() -> str:
    """
    Get system uptime.

    Returns:
        String representing system uptime in days, hours, minutes, and seconds.
    """
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    return str(uptime).split('.')[0]  # Remove microseconds
