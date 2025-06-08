"""
Tests for security validations module.
"""

import os
import stat
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ellma.security.validations import (
    check_file_permissions,
    check_directory_permissions,
    validate_network_access,
    validate_environment_security,
    FilePermissionError,
    NetworkAccessError
)


def test_check_file_permissions_secure(tmp_path):
    """Test checking secure file permissions."""
    # Create a test file with secure permissions
    test_file = tmp_path / "secure_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o600)  # rw-------
    
    # Should not raise an exception
    assert check_file_permissions(test_file) is True


def test_check_file_permissions_insecure(tmp_path):
    """Test checking insecure file permissions."""
    # Create a test file with insecure permissions
    test_file = tmp_path / "insecure_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o777)  # rwxrwxrwx
    
    # Should raise FilePermissionError
    with pytest.raises(FilePermissionError):
        check_file_permissions(test_file, max_permissions=0o600)


def test_check_directory_permissions(tmp_path):
    """Test checking directory permissions recursively."""
    # Create a test directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    test_dir.chmod(0o700)  # drwx------
    
    # Create a subdirectory and file
    subdir = test_dir / "subdir"
    subdir.mkdir()
    subdir.chmod(0o700)
    
    # Create files with different permissions
    secure_file = test_dir / "secure.txt"
    secure_file.write_text("secure")
    secure_file.chmod(0o600)  # rw-------
    
    # Create a file with group/other write permissions (insecure)
    insecure_file = test_dir / "insecure.txt"
    insecure_file.write_text("insecure")
    insecure_file.chmod(0o666)  # rw-rw-rw-
    
    # Create a file with group/other read permissions (insecure for sensitive files)
    readable_file = test_dir / "readable.txt"
    readable_file.write_text("readable")
    readable_file.chmod(0o644)  # rw-r--r--
    
    # Check permissions with strict settings (only owner should have any access)
    results = check_directory_permissions(test_dir, max_permissions=0o600, owner_only=True)
    
    # Debug output
    print("\nSecure items:")
    for item in sorted(results['secure']):
        print(f"- {item}")
    print("\nInsecure items:")
    for item in sorted(results['insecure']):
        print(f"- {item}")
    
    # Should find the secure file (directories are not included in 'secure' list)
    assert str(secure_file) in results['secure']
    
    # Should flag the insecure files and directories
    insecure_paths = [i.split(':', 1)[0].strip() for i in results['insecure']]
    
    # Check that insecure files are in the results
    assert str(insecure_file) in insecure_paths
    assert str(readable_file) in insecure_paths
    
    # Check that the test directory and subdirectory are in the insecure list
    assert any(str(test_dir) in path for path in insecure_paths)
    assert any('subdir' in path for path in insecure_paths)
    
    # Should have at least 4 insecure items (test_dir, subdir, insecure.txt, readable.txt)
    assert len(results['insecure']) >= 4
    
    # Check that the error message contains the expected permission info
    error_messages = '\n'.join(results['insecure']).lower()
    assert "insecure permissions" in error_messages or "permissions too permissive" in error_messages


@patch('ellma.security.validations.logger')
def test_validate_network_access(mock_logger):
    """Test network access validation."""
    # Test with default allowed ports
    assert validate_network_access() is True
    
    # Test with custom allowed domains and ports
    assert validate_network_access(
        allowed_domains=['example.com'],
        allowed_ports=[80, 443, 8000]
    ) is True
    
    # Should log the validation info
    assert mock_logger.info.called


def test_validate_environment_security(tmp_path):
    """Test environment security validation."""
    # Create a test file for checking
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o600)
    
    # Mock the important directories to include our test file
    with patch('ellma.security.validations.Path') as mock_path:
        # Mock Path.home()
        mock_home = MagicMock()
        mock_home.__truediv__.return_value = tmp_path
        
        # Configure the mock Path class
        mock_path.home.return_value = mock_home
        mock_path.side_effect = lambda *args: Path(*args)
        
        # Run the validation
        results = validate_environment_security()
    
    # Should have overall_secure status
    assert 'overall_secure' in results
    
    # Should have checked file permissions
    assert 'file_permissions' in results
    assert 'network_access' in results


def test_check_nonexistent_file():
    """Test checking permissions of a non-existent file."""
    with pytest.raises(FileNotFoundError):
        check_file_permissions("/nonexistent/file.txt")


def test_check_directory_permissions_nonexistent():
    """Test checking permissions of a non-existent directory."""
    with pytest.raises(FileNotFoundError):
        check_directory_permissions("/nonexistent/directory")
