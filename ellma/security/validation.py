"""
Security validations for ELLMa.

This module provides security validations for:
- File and directory permissions
- Network access controls
- Security-sensitive operations
"""

import os
import stat
import socket
import logging
import platform
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum

# Suppress pkg_resources deprecation warning
warnings.filterwarnings(
    action='ignore',
    category=DeprecationWarning,
    message='pkg_resources is deprecated.*',
    module='pkg_resources.*'
)

logger = logging.getLogger(__name__)

# Type variable for generics
T = TypeVar('T')

class SecurityCheckSeverity(Enum):
    """Severity levels for security findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityFinding:
    """Represents a security finding from a validation check."""
    check_name: str
    severity: SecurityCheckSeverity
    description: str
    details: Dict = None
    remediation: str = ""

class SecurityValidator:
    """Performs security validations on the system and environment."""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """Initialize the security validator.
        
        Args:
            project_root: Optional path to the project root directory.
        """
        self.project_root = Path(project_root) if project_root else None
        self._findings: List[SecurityFinding] = []
    
    def check_file_permissions(self, path: Union[str, Path], 
                             max_permissions: int = 0o600,
                             check_ownership: bool = True) -> bool:
        """Check file permissions and ownership.
        
        Args:
            path: Path to the file to check
            max_permissions: Maximum allowed permissions (octal)
            check_ownership: Whether to verify file ownership
            
        Returns:
            bool: True if file permissions are secure, False otherwise
        """
        try:
            path = Path(path)
            if not path.exists():
                self._add_finding(
                    check_name="file_not_found",
                    severity=SecurityCheckSeverity.MEDIUM,
                    description=f"File not found: {path}",
                    details={"path": str(path)},
                    remediation="Verify the file path exists and is accessible."
                )
                return False
                
            # Get file stats
            stat_info = path.stat()
            mode = stat.S_IMODE(stat_info.st_mode)
            
            # Check for any extra permissions beyond what's allowed
            extra_perms = mode & ~max_permissions
            if extra_perms != 0:
                self._add_finding(
                    check_name="insecure_file_permissions",
                    severity=SecurityCheckSeverity.HIGH,
                    description=f"Insecure file permissions on {path}",
                    details={
                        "path": str(path),
                        "current_permissions": oct(mode),
                        "extra_permissions": oct(extra_perms),
                        "max_allowed_permissions": oct(max_permissions)
                    },
                    remediation=f"Restrict file permissions using: chmod {oct(max_permissions)[-3:]} {path}"
                )
                return False
                
            # Check ownership if on Unix-like systems
            if check_ownership and hasattr(os, 'getuid') and hasattr(os, 'geteuid'):
                if stat_info.st_uid != os.geteuid():
                    self._add_finding(
                        check_name="suspicious_file_ownership",
                        severity=SecurityCheckSeverity.MEDIUM,
                        description=f"Suspicious file ownership for {path}",
                        details={
                            "path": str(path),
                            "owner_uid": stat_info.st_uid,
                            "current_uid": os.geteuid()
                        },
                        remediation=f"Change file ownership to the current user or verify file integrity."
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self._add_finding(
                check_name="file_permission_check_failed",
                severity=SecurityCheckSeverity.MEDIUM,
                description=f"Failed to check file permissions for {path}",
                details={"path": str(path), "error": str(e)}
            )
            return False
    
    def check_directory_permissions(self, path: Union[str, Path],
                                   max_permissions: int = 0o750,
                                   recursive: bool = False) -> bool:
        """Check directory permissions and optionally check contents recursively.
        
        Args:
            path: Path to the directory to check
            max_permissions: Maximum allowed permissions (octal)
            recursive: Whether to check files within the directory
            
        Returns:
            bool: True if directory permissions are secure, False otherwise
        """
        try:
            path = Path(path)
            if not path.exists() or not path.is_dir():
                self._add_finding(
                    check_name="directory_not_found",
                    severity=SecurityCheckSeverity.MEDIUM,
                    description=f"Directory not found: {path}",
                    details={"path": str(path)},
                    remediation="Verify the directory path exists and is accessible."
                )
                return False
                
            # Check directory permissions
            stat_info = path.stat()
            mode = stat.S_IMODE(stat_info.st_mode)
            
            # Check for any extra permissions beyond what's allowed
            extra_perms = mode & ~max_permissions
            if extra_perms != 0:
                self._add_finding(
                    check_name="insecure_directory_permissions",
                    severity=SecurityCheckSeverity.HIGH,
                    description=f"Insecure directory permissions on {path}",
                    details={
                        "path": str(path),
                        "current_permissions": oct(mode),
                        "extra_permissions": oct(extra_perms),
                        "max_allowed_permissions": oct(max_permissions)
                    },
                    remediation=f"Restrict directory permissions using: chmod {oct(max_permissions)[-3:]} {path}"
                )
                return False
                
            if recursive:
                # Recursively check contents
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        self.check_directory_permissions(
                            Path(root) / d,
                            max_permissions,
                            recursive=False
                        )
                    for f in files:
                        self.check_file_permissions(
                            Path(root) / f,
                            max_permissions=0o600  # Stricter for files
                        )
            
            return True
            
        except Exception as e:
            self._add_finding(
                check_name="directory_permission_check_failed",
                severity=SecurityCheckSeverity.MEDIUM,
                description=f"Failed to check directory permissions for {path}",
                details={"path": str(path), "error": str(e)}
            )
            return False
    
    def check_network_access(self, host: str, port: int,
                            allowed_hosts: Optional[Set[str]] = None) -> bool:
        """Check if network access to a host:port is allowed.
        
        Args:
            host: Target hostname or IP address
            port: Target port number
            allowed_hosts: Set of allowed host patterns (e.g., {'*.example.com', '192.168.1.*'})
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        try:
            # Resolve host to check if it's in allowed list
            if allowed_hosts:
                import fnmatch
                
                # Check if any allowed host pattern matches
                if not any(fnmatch.fnmatch(host, pattern) for pattern in allowed_hosts):
                    self._add_finding(
                        check_name="unauthorized_network_access",
                        severity=SecurityCheckSeverity.HIGH,
                        description=f"Unauthorized network access attempt to {host}:{port}",
                        details={
                            "host": host,
                            "port": port,
                            "allowed_hosts": list(allowed_hosts) if allowed_hosts else None
                        },
                        remediation="Update allowed_hosts to include this host if needed."
                    )
                    return False
            
            # Check if we can resolve the host
            try:
                socket.gethostbyname(host)
            except socket.gaierror:
                self._add_finding(
                    check_name="dns_resolution_failed",
                    severity=SecurityCheckSeverity.MEDIUM,
                    description=f"Failed to resolve host: {host}",
                    details={"host": host, "port": port}
                )
                return False
                
            # Check if port is open (non-blocking)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            
            try:
                result = sock.connect_ex((host, port))
                if result != 0:
                    self._add_finding(
                        check_name="network_connection_failed",
                        severity=SecurityCheckSeverity.MEDIUM,
                        description=f"Failed to connect to {host}:{port}",
                        details={"host": host, "port": port, "error_code": result}
                    )
                    return False
            finally:
                sock.close()
                
            return True
            
        except Exception as e:
            self._add_finding(
                check_name="network_check_failed",
                severity=SecurityCheckSeverity.MEDIUM,
                description=f"Network check failed for {host}:{port}",
                details={"host": host, "port": port, "error": str(e)}
            )
            return False
    
    def check_system_commands(self, commands: List[str],
                            allowed_commands: Optional[Set[str]] = None) -> bool:
        """Check if system commands are allowed to be executed.
        
        Args:
            commands: List of commands to check
            allowed_commands: Set of allowed command patterns (e.g., {'ls', 'git*'})
            
        Returns:
            bool: True if all commands are allowed, False otherwise
        """
        try:
            if not allowed_commands:
                return True
                
            import fnmatch
            
            for cmd in commands:
                # Get the base command (first part)
                base_cmd = cmd.split()[0] if cmd else ""
                
                # Check if any allowed pattern matches
                if not any(fnmatch.fnmatch(base_cmd, pattern) for pattern in allowed_commands):
                    self._add_finding(
                        check_name="unauthorized_command",
                        severity=SecurityCheckSeverity.HIGH,
                        description=f"Unauthorized command execution attempt: {cmd}",
                        details={
                            "command": cmd,
                            "allowed_commands": list(allowed_commands) if allowed_commands else None
                        },
                        remediation="Update allowed_commands to include this command if needed."
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self._add_finding(
                check_name="command_check_failed",
                severity=SecurityCheckSeverity.MEDIUM,
                description=f"Command check failed",
                details={"error": str(e)}
            )
            return False
    
    def validate_environment(self) -> bool:
        """Run all security validations.
        
        Returns:
            bool: True if all validations passed, False otherwise
        """
        if not self.project_root:
            self._add_finding(
                check_name="project_root_not_set",
                severity=SecurityCheckSeverity.MEDIUM,
                description="Project root directory not set",
                remediation="Initialize the SecurityValidator with a project root path."
            )
            return False
            
        # Check project directory permissions
        self.check_directory_permissions(
            self.project_root,
            max_permissions=0o750,
            recursive=True
        )
        
        # Check critical files
        critical_files = [
            self.project_root / 'pyproject.toml',
            self.project_root / 'poetry.lock',
            self.project_root / '.env',
            self.project_root / 'config.yaml',
        ]
        
        for file_path in critical_files:
            if file_path.exists():
                self.check_file_permissions(
                    file_path,
                    max_permissions=0o600
                )
        
        return len(self._findings) == 0
    
    def get_findings(self) -> List[SecurityFinding]:
        """Get all security findings.
        
        Returns:
            List[SecurityFinding]: List of security findings
        """
        return self._findings
    
    def clear_findings(self) -> None:
        """Clear all security findings."""
        self._findings = []
    
    def _add_finding(self, check_name: str, severity: SecurityCheckSeverity,
                   description: str, details: Dict = None, remediation: str = "") -> None:
        """Add a security finding.
        
        Args:
            check_name: Name of the security check
            severity: Severity level
            description: Description of the finding
            details: Additional details about the finding
            remediation: Recommended remediation steps
        """
        finding = SecurityFinding(
            check_name=check_name,
            severity=severity,
            description=description,
            details=details or {},
            remediation=remediation
        )
        self._findings.append(finding)
        
        # Log the finding
        log_msg = f"[Security] {severity.value.upper()}: {check_name} - {description}"
        if details:
            log_msg += f"\nDetails: {details}"
        if remediation:
            log_msg += f"\nRemediation: {remediation}"
            
        if severity in [SecurityCheckSeverity.HIGH, SecurityCheckSeverity.CRITICAL]:
            logger.error(log_msg)
        elif severity == SecurityCheckSeverity.MEDIUM:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

# Global instance for convenience
security_validator = SecurityValidator()

def validate_security() -> bool:
    """Run security validations and return status."""
    return security_validator.validate_environment()

def get_security_findings() -> List[SecurityFinding]:
    """Get all security findings."""
    return security_validator.get_findings()

def clear_security_findings() -> None:
    """Clear all security findings."""
    security_validator.clear_findings()
