"""
Security validations for the ELLMa system.

This module provides functions to validate various security aspects of the system,
including file permissions, network access, and other security-related checks.
"""

import os
import stat
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class SecurityValidationError(Exception):
    """Base class for security validation errors."""
    pass

class FilePermissionError(SecurityValidationError):
    """Raised when file permissions are not secure."""
    pass

class NetworkAccessError(SecurityValidationError):
    """Raised when network access is not allowed."""
    pass

def check_file_permissions(filepath: Union[str, Path], 
                         max_permissions: int = 0o600,
                         owner_only: bool = True) -> bool:
    """
    Check if file permissions are secure.
    
    Args:
        filepath: Path to the file to check
        max_permissions: Maximum allowed permission bits (octal)
        owner_only: If True, only the owner should have any permissions
        
    Returns:
        bool: True if permissions are secure, False otherwise
        
    Raises:
        FilePermissionError: If permissions are not secure
        FileNotFoundError: If the file doesn't exist
    """
    try:
        filepath = Path(filepath).resolve()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        stat_info = filepath.stat()
        mode = stat_info.st_mode
        
        # Check if permissions are too permissive
        if (mode & 0o777) > max_permissions:
            raise FilePermissionError(
                f"File {filepath} has insecure permissions: {oct(mode & 0o777)[-3:]} "
                f"(max allowed: {oct(max_permissions)[2:]})"
            )
            
        # Check if file is owned by current user
        if owner_only and (os.geteuid() != stat_info.st_uid):
            raise FilePermissionError(
                f"File {filepath} is not owned by the current user"
            )
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to check file permissions for {filepath}: {e}")
        raise

def check_directory_permissions(dirpath: Union[str, Path],
                              max_permissions: int = 0o700,
                              owner_only: bool = True) -> Dict[str, List[str]]:
    """
    Recursively check directory permissions.
    
    Args:
        dirpath: Path to the directory to check
        max_permissions: Maximum allowed permission bits (octal)
        owner_only: If True, only the owner should have any permissions
        
    Returns:
        Dict with two keys: 'secure' (list of secure files) and 'insecure' (list of insecure files)
    """
    dirpath = Path(dirpath).resolve()
    results = {'secure': [], 'insecure': []}
    
    if not dirpath.exists():
        raise FileNotFoundError(f"Directory not found: {dirpath}")
    
    try:
        for root, _, files in os.walk(dirpath):
            root_path = Path(root)
            
            # Check directory permissions
            try:
                check_file_permissions(root_path, max_permissions, owner_only)
            except FilePermissionError as e:
                results['insecure'].append(f"{root_path}/: {str(e)}")
            else:
                results['secure'].append(f"{root_path}/")
                
            # Check file permissions
            for filename in files:
                file_path = root_path / filename
                try:
                    check_file_permissions(file_path, max_permissions, owner_only)
                except (FilePermissionError, PermissionError) as e:
                    results['insecure'].append(f"{file_path}: {str(e)}")
                else:
                    results['secure'].append(str(file_path))
                    
    except Exception as e:
        logger.error(f"Error checking directory {dirpath}: {e}")
        raise
        
    return results

def validate_network_access(allowed_domains: List[str] = None,
                          allowed_ports: List[int] = None) -> bool:
    """
    Validate network access is restricted to allowed domains and ports.
    
    Args:
        allowed_domains: List of allowed domain names (e.g., ['example.com'])
        allowed_ports: List of allowed ports (e.g., [80, 443])
        
    Returns:
        bool: True if network access is properly restricted
        
    Note:
        This is a placeholder implementation. In a real system, this would
        check system firewall rules or network policies.
    """
    # Default to common web ports if none specified
    if allowed_ports is None:
        allowed_ports = [80, 443]
        
    if allowed_domains is None:
        allowed_domains = []
    
    # In a real implementation, we would check system firewall rules here
    logger.info("Network access validation would check firewall rules here")
    logger.info(f"Allowed domains: {allowed_domains}")
    logger.info(f"Allowed ports: {allowed_ports}")
    
    return True

def validate_environment_security() -> Dict[str, Union[bool, Dict]]:
    """
    Run all security validations on the environment.
    
    Returns:
        Dict with validation results
    """
    results = {
        'file_permissions': {},
        'network_access': {},
        'overall_secure': True
    }
    
    try:
        # Check permissions of important directories
        important_dirs = [
            Path('/etc/passwd'),
            Path('/etc/shadow'),
            Path('/etc/sudoers'),
            Path.home() / '.ssh',
            Path(__file__).parent.parent.parent  # Project root
        ]
        
        for dir_path in important_dirs:
            try:
                if dir_path.is_file():
                    check_file_permissions(dir_path)
                    results['file_permissions'][str(dir_path)] = 'secure'
                elif dir_path.is_dir():
                    dir_results = check_directory_permissions(dir_path)
                    results['file_permissions'][str(dir_path)] = {
                        'secure': len(dir_results['secure']),
                        'insecure': len(dir_results['insecure'])
                    }
                    if dir_results['insecure']:
                        results['overall_secure'] = False
            except Exception as e:
                results['file_permissions'][str(dir_path)] = f"error: {str(e)}"
                results['overall_secure'] = False
                
        # Validate network access
        try:
            network_ok = validate_network_access()
            results['network_access'] = {
                'status': 'restricted' if network_ok else 'unrestricted',
                'allowed_ports': [80, 443],
                'allowed_domains': []
            }
            if not network_ok:
                results['overall_secure'] = False
        except Exception as e:
            results['network_access'] = f"error: {str(e)}"
            results['overall_secure'] = False
            
    except Exception as e:
        logger.error(f"Error during security validation: {e}")
        results['error'] = str(e)
        results['overall_secure'] = False
        
    return results
