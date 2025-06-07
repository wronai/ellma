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
    
    secure_file = test_dir / "secure.txt"
    secure_file.write_text("secure")
    secure_file.chmod(0o600)  # rw-------
    
    insecure_file = test_dir / "insecure.txt"
    insecure_file.write_text("insecure")
    insecure_file.chmod(0o666)  # rw-rw-rw-
    
    # Check permissions
    results = check_directory_permissions(test_dir)
    
    # Debug output
    print("\nSecure items:")
    for item in sorted(results['secure']):
        print(f"- {item}")
    print("\nInsecure items:")
    for item in sorted(results['insecure']):
        print(f"- {item}")
    
    # Should find all secure and insecure items
    # The exact count might vary based on the test environment
    assert len(results['secure']) >= 2  # At least the directory and secure file
    assert len(results['insecure']) == 1  # The insecure file
    
    # Specific checks for expected items
    assert str(test_dir) + '/' in results['secure']
    assert str(secure_file) in results['secure']
    assert str(insecure_file) in [i.split(':')[0] for i in results['insecure']]


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
