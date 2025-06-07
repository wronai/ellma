"""
Tests for security validation module.
"""

import os
import stat
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the validation module
try:
    from ellma.security.validation import (
        SecurityValidator,
        SecurityCheckSeverity,
        SecurityFinding
    )
    HAS_DEPENDENCIES = True
except ImportError as e:
    HAS_DEPENDENCIES = False

# Skip all tests if dependencies are not available
pytestmark = pytest.mark.skipif(
    not HAS_DEPENDENCIES,
    reason="Skipping all tests due to missing dependencies"
)

# Skip network tests by default to avoid external dependencies
SKIP_NETWORK_TESTS = os.environ.get('SKIP_NETWORK_TESTS', '1') == '1'

# Only run the test if we have the required dependencies
if HAS_DEPENDENCIES:
    # Define test constants
    TEST_SEVERITY_LEVELS = [
        (SecurityCheckSeverity.LOW, "INFO"),
        (SecurityCheckSeverity.MEDIUM, "WARNING"),
        (SecurityCheckSeverity.HIGH, "ERROR"),
        (SecurityCheckSeverity.CRITICAL, "ERROR"),
    ]
else:
    # Define empty test constants if dependencies are missing
    TEST_SEVERITY_LEVELS = []

@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
def test_check_file_permissions_secure(tmp_path):
    """Test checking secure file permissions."""
    # Create a test file with secure permissions
    test_file = tmp_path / "secure_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o600)  # rw-------
    
    validator = SecurityValidator()
    assert validator.check_file_permissions(test_file) is True
    assert len(validator.get_findings()) == 0


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
def test_check_file_permissions_insecure(tmp_path):
    """Test checking insecure file permissions."""
    # Create a test file with insecure permissions
    test_file = tmp_path / "insecure_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o666)  # rw-rw-rw-
    
    validator = SecurityValidator()
    assert validator.check_file_permissions(test_file, max_permissions=0o600) is False
    
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "insecure_file_permissions" in findings[0].check_name


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
def test_check_directory_permissions_secure(tmp_path):
    """Test checking secure directory permissions."""
    # Create a test directory with secure permissions
    test_dir = tmp_path / "secure_dir"
    test_dir.mkdir()
    test_dir.chmod(0o750)  # rwxr-x---
    
    validator = SecurityValidator()
    assert validator.check_directory_permissions(test_dir) is True
    assert len(validator.get_findings()) == 0


@pytest.mark.skipif(not HAS_DEPENDENCIES or SKIP_NETWORK_TESTS, 
                  reason="Missing dependencies or network tests disabled")
def test_check_network_access_allowed():
    """Test checking allowed network access."""
    validator = SecurityValidator()
    
    # Mock socket to simulate successful connection to example.com
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 0
        
        # Test with allowed host pattern
        assert validator.check_network_access(
            "example.com", 80, 
            allowed_hosts={"*.com", "example.*"}
        ) is True
        
        # No findings should be generated for allowed access
        assert len(validator.get_findings()) == 0


@pytest.mark.skipif(not HAS_DEPENDENCIES or SKIP_NETWORK_TESTS,
                  reason="Missing dependencies or network tests disabled")
def test_check_network_access_unauthorized():
    """Test checking unauthorized network access."""
    validator = SecurityValidator()
    
    # Test with disallowed host
    assert validator.check_network_access(
        "example.com", 80,
        allowed_hosts={"*.internal", "192.168.*"}
    ) is False
    
    # Should generate a finding for unauthorized access
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "unauthorized_network_access" in findings[0].check_name


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
def test_validate_environment(tmp_path, monkeypatch):
    """Test the full environment validation.
    
    This test verifies that the validator correctly identifies and reports
    insecure file permissions. We mock the file stats to simulate different
    permission scenarios.
    """
    # Create test files
    pyproject = tmp_path / "pyproject.toml"
    pyproject.touch()
    
    poetry_lock = tmp_path / "poetry.lock"
    poetry_lock.touch()
    
    env_file = tmp_path / ".env"
    env_file.touch()
    
    config_file = tmp_path / "config.yaml"
    config_file.touch()
    
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    # Create a mock for os.stat to control file permissions
    class MockStat:
        def __init__(self, mode):
            self.st_mode = mode
    
    # Mock os.stat to return our controlled permissions
    def mock_stat(path, *args, **kwargs):
        path = str(path)
        if 'pyproject.toml' in path or 'poetry.lock' in path or '.env' in path or 'config.yaml' in path:
            # Return secure file permissions (0o600)
            return MockStat(0o100600)  # Regular file with 600 permissions
        elif 'src' in path and os.path.isdir(path):
            # Return secure directory permissions (0o750)
            return MockStat(0o040750)  # Directory with 750 permissions
        return os.stat(path, *args, **kwargs)
    
    # Apply the mock
    monkeypatch.setattr('os.stat', mock_stat)
    
    # Create validator and run validation
    validator = SecurityValidator(project_root=tmp_path)
    result = validator.validate_environment()
    findings = validator.get_findings()
    
    # Verify the results
    assert result is True, f"Validation should pass with secure permissions. Findings: {findings}"
    assert len(findings) == 0, f"No findings should be reported for secure permissions. Found: {findings}"


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
def test_validate_environment_insecure(tmp_path):
    """Test environment validation with insecure permissions."""
    # Create test files with insecure permissions
    (tmp_path / "pyproject.toml").touch(mode=0o666)
    (tmp_path / ".env").touch(mode=0o666)
    
    validator = SecurityValidator(project_root=tmp_path)
    assert validator.validate_environment() is False
    
    # Should find insecure file permissions
    findings = validator.get_findings()
    assert len(findings) >= 2  # At least two findings (one for each file)
    assert any(f.severity == SecurityCheckSeverity.HIGH for f in findings)


def test_severity_logging(caplog):
    """Test that findings are logged with appropriate log levels."""
    # Skip if we don't have the required dependencies
    if not HAS_DEPENDENCIES:
        pytest.skip("Missing required dependencies")
        
    # Define test cases with severity and expected log level
    test_cases = [
        (SecurityCheckSeverity.LOW, "INFO"),
        (SecurityCheckSeverity.MEDIUM, "WARNING"),
        (SecurityCheckSeverity.HIGH, "ERROR"),
        (SecurityCheckSeverity.CRITICAL, "ERROR"),
    ]
    
    for severity, expected_log_level in test_cases:
        caplog.clear()  # Clear previous logs
        validator = SecurityValidator()
        
        with caplog.at_level("INFO"):
            validator._add_finding(
                check_name="test_check",
                severity=severity,
                description="Test finding",
                remediation="Fix it"
            )
        
        assert len(caplog.records) == 1, f"Expected 1 log record for {severity}, got {len(caplog.records)}"
        record = caplog.records[0]
        assert record.levelname == expected_log_level, \
            f"Expected level {expected_log_level} for {severity}, got {record.levelname}"
        assert "Test finding" in record.message, "Test finding not in log message"
        assert "Fix it" in record.message, "Remediation not in log message"


def test_check_system_commands():
    """Test checking system command permissions."""
    validator = SecurityValidator()
    
    # Test with allowed commands
    assert validator.check_system_commands(
        ["ls -la", "git status"],
        allowed_commands={"ls", "git*"}
    ) is True
    
    # Test with unauthorized command
    assert validator.check_system_commands(
        ["rm -rf /"],
        allowed_commands={"ls", "git*"}
    ) is False
    
    # Should find unauthorized command
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "unauthorized_command" in findings[0].check_name

def test_check_file_permissions_insecure(tmp_path):
    """Test checking insecure file permissions."""
    # Create a test file with insecure permissions
    test_file = tmp_path / "insecure_file.txt"
    test_file.write_text("test")
    test_file.chmod(0o666)  # rw-rw-rw-
    
    validator = SecurityValidator()
    assert validator.check_file_permissions(test_file, max_permissions=0o600) is False
    
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "insecure_file_permissions" in findings[0].check_name

def test_check_directory_permissions_secure(tmp_path):
    """Test checking secure directory permissions."""
    # Create a test directory with secure permissions
    test_dir = tmp_path / "secure_dir"
    test_dir.mkdir()
    test_dir.chmod(0o750)  # rwxr-x---
    
    validator = SecurityValidator()
    assert validator.check_directory_permissions(test_dir) is True
    assert len(validator.get_findings()) == 0

def test_check_network_access_allowed():
    """Test checking allowed network access."""
    validator = SecurityValidator()
    
    # Mock socket to simulate successful connection to example.com
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 0
        
        # Test with allowed host pattern
        assert validator.check_network_access(
            "example.com", 80, 
            allowed_hosts={"*.com", "example.*"}
        ) is True
        
        # No findings should be generated for allowed access
        assert len(validator.get_findings()) == 0

def test_check_network_access_unauthorized():
    """Test checking unauthorized network access."""
    validator = SecurityValidator()
    
    # Test with disallowed host
    assert validator.check_network_access(
        "example.com", 80,
        allowed_hosts={"*.internal", "192.168.*"}
    ) is False
    
    # Should generate a finding for unauthorized access
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "unauthorized_network_access" in findings[0].check_name

def test_validate_environment(tmp_path):
    """Test the full environment validation."""
    # Create a test project structure
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "poetry.lock").touch()
    
    # Create a test .env file with secure permissions
    env_file = tmp_path / ".env"
    env_file.touch()
    env_file.chmod(0o600)
    
    # Create a test config file with secure permissions
    config_file = tmp_path / "config.yaml"
    config_file.touch()
    config_file.chmod(0o600)
    
    # Create a test directory with secure permissions
    (tmp_path / "src").mkdir()
    (tmp_path / "src").chmod(0o750)
    
    validator = SecurityValidator(project_root=tmp_path)
    assert validator.validate_environment() is True
    assert len(validator.get_findings()) == 0

def test_validate_environment_insecure(tmp_path):
    """Test environment validation with insecure permissions."""
    # Create test files with insecure permissions
    (tmp_path / "pyproject.toml").touch(mode=0o666)
    (tmp_path / ".env").touch(mode=0o666)
    
    validator = SecurityValidator(project_root=tmp_path)
    assert validator.validate_environment() is False
    
    # Should find insecure file permissions
    findings = validator.get_findings()
    assert len(findings) >= 2  # At least two findings (one for each file)
    assert any(f.severity == SecurityCheckSeverity.HIGH for f in findings)

@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Missing required dependencies")
@pytest.mark.parametrize("severity,expected_log_level", TEST_SEVERITY_LEVELS)
def test_severity_logging(severity, expected_log_level, caplog):
    """Test that findings are logged with appropriate log levels."""
    validator = SecurityValidator()
    
    with caplog.at_level("INFO"):
        validator._add_finding(
            check_name="test_check",
            severity=severity,
            description="Test finding",
            remediation="Fix it"
        )
    
    assert len(caplog.records) == 1
    record = caplog.records[0]
    # Strip ANSI color codes from the levelname for comparison
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]+m')
    clean_levelname = ansi_escape.sub('', record.levelname)
    assert clean_levelname == expected_log_level, f"Expected {expected_log_level} but got {clean_levelname}"
    assert "Test finding" in record.message
    assert "Fix it" in record.message

def test_check_system_commands():
    """Test checking system command permissions."""
    validator = SecurityValidator()
    
    # Test with allowed commands
    assert validator.check_system_commands(
        ["ls -la", "git status"],
        allowed_commands={"ls", "git*"}
    ) is True
    
    # Test with unauthorized command
    assert validator.check_system_commands(
        ["rm -rf /"],
        allowed_commands={"ls", "git*"}
    ) is False
    
    # Should find unauthorized command
    findings = validator.get_findings()
    assert len(findings) == 1
    assert findings[0].severity == SecurityCheckSeverity.HIGH
    assert "unauthorized_command" in findings[0].check_name
