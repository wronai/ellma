"""
Network ports command.

This module provides the `ports` command which lists network connections and open ports.
"""

from typing import Dict, Any, List, Optional, Tuple
import socket
import psutil
from ipaddress import ip_address

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..commands import BaseCommand, CommandResult
from ...core import get_network_info

class PortsCommand(BaseCommand):
    """List network connections and open ports."""
    
    def execute(self, 
               listening_only: bool = True,
               resolve: bool = False,
               process_info: bool = False,
               *args, **kwargs) -> CommandResult:
        """Execute the ports command.
        
        Args:
            listening_only: Only show listening ports.
            resolve: Resolve IP addresses to hostnames.
            process_info: Show process information.
            
        Returns:
            CommandResult: Contains network connection information.
        """
        try:
            # Get network connections
            connections = self._get_connections(listening_only, resolve, process_info)
            
            # Display connections
            self._display_connections(connections, process_info)
            
            return CommandResult(success=True, data={"connections": connections})
            
        except Exception as e:
            error_msg = f"Failed to list network connections: {str(e)}"
            self.console.print(f"[red]Error:[/red] {error_msg}")
            return CommandResult(success=False, error=error_msg)
    
    def _get_connections(self, listening_only: bool, resolve: bool, process_info: bool) -> List[Dict[str, Any]]:
        """Get network connections with optional filtering and resolution.
        
        Args:
            listening_only: Only include listening connections.
            resolve: Resolve IP addresses to hostnames.
            process_info: Include process information.
            
        Returns:
            List of connection dictionaries.
        """
        connections = []
        
        # Get all connections
        for conn in psutil.net_connections(kind='inet'):
            try:
                # Skip if listening_only is True and connection is not listening
                if listening_only and conn.status != 'LISTEN':
                    continue
                
                # Skip connections without local address
                if not hasattr(conn, 'laddr') or not conn.laddr:
                    continue
                
                connection = {
                    "protocol": self._get_protocol(conn.family, conn.type),
                    "local_address": self._format_address(conn.laddr, resolve),
                    "local_port": conn.laddr.port,
                    "status": conn.status
                }
                
                # Add remote address if available
                if hasattr(conn, 'raddr') and conn.raddr:
                    connection.update({
                        "remote_address": self._format_address(conn.raddr, resolve),
                        "remote_port": conn.raddr.port
                    })
                
                # Add process info if requested and available
                if process_info and hasattr(conn, 'pid') and conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        with proc.oneshot():
                            connection.update({
                                "pid": conn.pid,
                                "process_name": proc.name(),
                                "process_cmdline": " ".join(proc.cmdline()),
                                "process_username": proc.username(),
                                "process_status": proc.status()
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        connection["pid"] = conn.pid
                        connection["process_info"] = "[not found]"
                
                connections.append(connection)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return connections
    
    def _get_protocol(self, family: int, type_: int) -> str:
        """Get protocol name from socket family and type.
        
        Args:
            family: Socket family (e.g., socket.AF_INET).
            type_: Socket type (e.g., socket.SOCK_STREAM).
            
        Returns:
            Protocol name as string.
        """
        if family == socket.AF_INET or family == socket.AF_INET6:
            if type_ == socket.SOCK_STREAM:
                return "TCP"
            elif type_ == socket.SOCK_DGRAM:
                return "UDP"
            elif type_ == socket.SOCK_RAW:
                return "IP"
        
        # Fallback to string representation
        try:
            return f"{socket.AddressFamily(family).name}/{socket.SocketKind(type_).name}"
        except (ValueError, AttributeError):
            return f"Unknown ({family}/{type_})"
    
    def _format_address(self, addr: Any, resolve: bool = False) -> str:
        """Format a network address.
        
        Args:
            addr: Address object with ip and port attributes.
            resolve: Whether to resolve IP to hostname.
            
        Returns:
            Formatted address string.
        """
        if not hasattr(addr, 'ip') or not addr.ip:
            return ""
        
        ip = addr.ip
        
        # Handle IPv6 addresses
        if ':' in ip and not ip.startswith('['):
            ip = f"[{ip}]"
        
        # Resolve IP to hostname if requested
        if resolve:
            try:
                hostname = socket.getnameinfo((addr.ip, 0), 0)[0]
                if hostname != addr.ip:  # Only use if we got a real hostname
                    return f"{hostname} ({ip})"
            except (socket.gaierror, socket.herror, socket.timeout):
                pass
        
        return ip
    
    def _display_connections(self, connections: List[Dict[str, Any]], show_process_info: bool = False) -> None:
        """Display network connections in a table.
        
        Args:
            connections: List of connection dictionaries.
            show_process_info: Whether to show process information.
        """
        if not connections:
            self.console.print("[yellow]No network connections found.[/yellow]")
            return
        
        # Create table
        table = Table(
            title="Network Connections",
            show_header=True,
            header_style="bold magenta",
            box=None
        )
        
        # Add columns
        table.add_column("Proto", style="cyan")
        table.add_column("Local Address", style="green")
        table.add_column("Foreign Address", style="yellow")
        table.add_column("Status", style="blue")
        
        if show_process_info:
            table.add_column("PID/Program", style="magenta")
        
        # Add rows
        for conn in connections:
            # Format local address
            local_addr = f"{conn['local_address']}:{conn['local_port']}"
            
            # Format remote address if available
            remote_addr = ""
            if 'remote_address' in conn and 'remote_port' in conn:
                remote_addr = f"{conn['remote_address']}:{conn['remote_port']}"
            
            # Format status
            status = conn.get('status', '').upper()
            
            # Format process info if available
            process_info = ""
            if show_process_info:
                if 'process_name' in conn:
                    process_info = f"{conn.get('pid', '')}/{conn['process_name']}"
                elif 'pid' in conn:
                    process_info = str(conn['pid'])
            
            # Add row to table
            row = [
                conn['protocol'],
                local_addr,
                remote_addr,
                status
            ]
            
            if show_process_info:
                row.append(process_info)
            
            table.add_row(*row)
        
        # Display table
        self.console.print(table)
        
        # Show summary
        total = len(connections)
        listening = sum(1 for c in connections if c.get('status') == 'LISTEN')
        established = sum(1 for c in connections if c.get('status') == 'ESTABLISHED')
        
        self.console.print(f"[dim]Total: {total} connections ({listening} listening, {established} established)[/dim]")
        
        # Show common ports information
        self._display_common_ports(connections)
    
    def _display_common_ports(self, connections: List[Dict[str, Any]]) -> None:
        """Display information about common ports.
        
        Args:
            connections: List of connection dictionaries.
        """
        # Common ports and their services
        common_ports = {
            20: "FTP (Data)",
            21: "FTP (Control)",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            67: "DHCP Server",
            68: "DHCP Client",
            69: "TFTP",
            80: "HTTP",
            88: "Kerberos",
            110: "POP3",
            111: "RPC",
            119: "NNTP",
            123: "NTP",
            135: "MS RPC",
            137: "NetBIOS Name",
            138: "NetBIOS Datagram",
            139: "NetBIOS Session",
            143: "IMAP",
            161: "SNMP",
            162: "SNMP Trap",
            179: "BGP",
            194: "IRC",
            389: "LDAP",
            443: "HTTPS",
            445: "SMB",
            465: "SMTPS",
            514: "Syslog",
            515: "LPD",
            587: "SMTP (Submission)",
            631: "IPP (Printing)",
            636: "LDAPS",
            873: "rsync",
            902: "VMware Server",
            989: "FTPS (Data)",
            990: "FTPS (Control)",
            993: "IMAPS",
            995: "POP3S",
            1080: "SOCKS Proxy",
            1194: "OpenVPN",
            1433: "MS SQL Server",
            1521: "Oracle DB",
            1723: "PPTP",
            2049: "NFS",
            2082: "cPanel",
            2083: "cPanel SSL",
            2086: "WHM",
            2087: "WHM SSL",
            2095: "Webmail",
            2096: "Webmail SSL",
            2181: "ZooKeeper",
            2375: "Docker",
            2376: "Docker TLS",
            2377: "Docker Swarm",
            2380: "etcd",
            2483: "Oracle DB SSL",
            2484: "Oracle DB",
            3000: "Node.js",
            3128: "Squid",
            3268: "Microsoft Global Catalog",
            3269: "Microsoft Global Catalog SSL",
            3306: "MySQL",
            3389: "RDP",
            3690: "Subversion",
            4369: "Erlang Port Mapper",
            5000: "UPnP",
            5001: "Synology",
            5432: "PostgreSQL",
            5500: "VNC Server",
            5601: "Kibana",
            5672: "RabbitMQ",
            5900: "VNC",
            5938: "TeamViewer",
            5984: "CouchDB",
            6000: "X11",
            6379: "Redis",
            6443: "Kubernetes API Server",
            6666: "IRC",
            7001: "WebLogic",
            7002: "WebLogic SSL",
            7077: "Spark",
            7199: "Cassandra",
            7474: "Neo4j",
            7687: "Neo4j Bolt",
            8000: "HTTP Alt",
            8005: "Tomcat Shutdown",
            8008: "HTTP Alt",
            8009: "AJP",
            8020: "HDFS",
            8042: "Hadoop NodeManager",
            8080: "HTTP Proxy",
            8081: "HTTP Proxy Alt",
            8088: "Hadoop ResourceManager",
            8089: "Splunk",
            8090: "Atlassian",
            8091: "Couchbase",
            8092: "Couchbase SSL",
            8096: "Plex",
            8140: "Puppet",
            8200: "GoCD",
            8222: "VMware Authd",
            8243: "HTTPS Alt",
            8333: "Bitcoin",
            8400: "Commvault",
            8443: "HTTPS Alt",
            8500: "Consul",
            8530: "WSUS",
            8531: "WSUS SSL",
            8761: "Eureka",
            8888: "Jupyter",
            8983: "Solr",
            9000: "SonarQube",
            9001: "Tor",
            9042: "Cassandra Native",
            9060: "WebLogic Console",
            9080: "WebSphere",
            9090: "Prometheus",
            9092: "Kafka",
            9100: "Node Exporter",
            9160: "Cassandra Thrift",
            9200: "Elasticsearch",
            9300: "Elasticsearch Transport",
            9411: "Git",
            9443: "VMware vSphere",
            9999: "JIRA",
            10000: "Webmin",
            10050: "Zabbix Agent",
            10051: "Zabbix Server",
            10250: "Kubelet",
            10255: "Kubelet Read-Only",
            10256: "Kube Proxy",
            11211: "Memcached",
            12017: "MongoDB",
            12201: "Splunk",
            12489: "NSClient++",
            15672: "RabbitMQ Management",
            16379: "Redis Sentinel",
            16509: "Kubernetes API",
            18080: "Jenkins",
            20000: "Docker Swarm",
            20720: "Symantec AV",
            24800: "Synergy",
            25565: "Minecraft",
            27017: "MongoDB",
            27018: "MongoDB SSL",
            27019: "MongoDB Shard",
            28015: "RethinkDB",
            28017: "MongoDB Web",
            30000: "Kubernetes NodePort",
            31337: "Back Orifice",
            32768: "RPC",
            37777: "Dahua CCTV",
            50000: "SAP",
            50070: "Hadoop NameNode",
            50075: "Hadoop DataNode",
            50090: "Hadoop SecondaryNameNode",
            54328: "PostgreSQL",
            60010: "HBase Master"
        }
        
        # Find common ports in use
        common_in_use = {}
        for conn in connections:
            port = conn.get('local_port')
            if port and port in common_ports and port not in common_in_use:
                common_in_use[port] = common_ports[port]
        
        # Display common ports if any
        if common_in_use:
            self.console.print("\n[bold]Common Ports in Use:[/bold]")
            for port, service in sorted(common_in_use.items()):
                self.console.print(f"  [cyan]{port:>5}[/cyan] - {service}")

def execute(listening_only: bool = True, resolve: bool = False, process_info: bool = False, *args, **kwargs) -> CommandResult:
    """Execute the ports command.
    
    This is the entry point for the ports command.
    
    Args:
        listening_only: Only show listening ports.
        resolve: Resolve IP addresses to hostnames.
        process_info: Show process information.
        
    Returns:
        CommandResult: The result of the command execution.
    """
    return PortsCommand().execute(
        listening_only=listening_only,
        resolve=resolve,
        process_info=process_info,
        *args,
        **kwargs
    )
