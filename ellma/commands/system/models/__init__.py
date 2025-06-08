"""
Data models for system commands.

This module contains the data models used throughout the system commands module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

@dataclass
class SystemInfo:
    """System information data model."""
    hostname: str
    platform: Dict[str, str]
    hardware: Dict[str, Any]
    resources: Dict[str, Any]
    network: Dict[str, Any]
    storage: Dict[str, Any]
    processes: Dict[str, Any]
    services: Dict[str, Any]
    security: Dict[str, Any]
    health_score: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ProcessInfo:
    """Process information data model."""
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    create_time: float
    runtime: str
    runtime_str: str

@dataclass
class NetworkConnection:
    """Network connection information data model."""
    protocol: str
    local_address: str
    remote_address: str
    status: str
    pid: Optional[int] = None
    process_name: Optional[str] = None

@dataclass
class ServiceInfo:
    """Service information data model."""
    name: str
    load: str
    active: str
    sub: str
    description: str = ""

@dataclass
class HealthStatus:
    """System health status data model."""
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    load_average: List[float]
    uptime: str
    processes_count: int
    alerts: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MonitoringData:
    """System monitoring data model."""
    timestamps: List[str] = field(default_factory=list)
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    disk_io: List[Dict[str, float]] = field(default_factory=list)
    network_io: List[Dict[str, float]] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)
