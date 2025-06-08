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
    
    # Track which paths should be treated as files vs directories
    test_files = {str(pyproject), str(poetry_lock), str(env_file), str(config_file)}
    test_dirs = {str(src_dir)}
    
    # Mock os.path.isfile and os.path.isdir
    def mock_isfile(path):
        path = str(path)
        return path in test_files or any(f in path for f in test_files)
    
    def mock_isdir(path):
        path = str(path)
        return path in test_dirs or any(d in path for d in test_dirs)
    
    # Mock os.stat to return our controlled permissions
    def mock_stat(path, *args, **kwargs):
        path = str(path)
        if any(f in path for f in test_files):
            # Return secure file permissions (0o600)
            return MockStat(0o100600)  # Regular file with 600 permissions
        elif any(d in path for d in test_dirs):
            # Return secure directory permissions (0o750)
            return MockStat(0o040750)  # Directory with 750 permissions
        return os.stat(path, *args, **kwargs)
    
    # Apply the mocks
    monkeypatch.setattr('os.stat', mock_stat)
    monkeypatch.setattr('os.path.isfile', mock_isfile)
    monkeypatch.setattr('os.path.isdir', mock_isdir)
    
    # Create validator and run validation
    validator = SecurityValidator(project_root=tmp_path)
    result = validator.validate_environment()
    findings = validator.get_findings()
    
    # Verify the results
    error_msg = (
        f"Validation should pass with secure permissions. "
        f"Result: {result}, Findings: {findings}"
    )
    assert result is True, error_msg
    assert len(findings) == 0, error_msg


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

def test_validate_environment(tmp_path, monkeypatch):
    """Test the full environment validation."""
    # Create a test project structure with secure permissions
    pyproject = tmp_path / "pyproject.toml"
    pyproject.touch(mode=0o600)
    
    poetry_lock = tmp_path / "poetry.lock"
    poetry_lock.touch(mode=0o600)
    
    # Create a test .env file with secure permissions
    env_file = tmp_path / ".env"
    env_file.touch(mode=0o600)
    
    # Create a test config file with secure permissions
    config_file = tmp_path / "config.yaml"
    config_file.touch(mode=0o600)
    
    # Create a test directory with secure permissions
    src_dir = tmp_path / "src"
    src_dir.mkdir(mode=0o750)
    
    # Verify permissions were set correctly
    assert (pyproject.stat().st_mode & 0o777) == 0o600
    assert (poetry_lock.stat().st_mode & 0o777) == 0o600
    assert (env_file.stat().st_mode & 0o777) == 0o600
    assert (config_file.stat().st_mode & 0o777) == 0o600
    assert (src_dir.stat().st_mode & 0o777) == 0o750
    
    # Create validator and run validation
    validator = SecurityValidator(project_root=tmp_path)
    
    # Run validation and capture results
    result = validator.validate_environment()
    findings = validator.get_findings()
    
    # Print findings if validation failed
    if not result or findings:
        print("\n=== Validation Failed ===")
        print(f"Result: {result}")
        print(f"Number of findings: {len(findings)}")
        for i, finding in enumerate(findings, 1):
            print(f"\nFinding {i}:")
            print(f"- Check: {finding.check_name}")
            print(f"- Severity: {finding.severity}")
            print(f"- Description: {finding.description}")
            if hasattr(finding, 'details'):
                print("- Details:", finding.details)
            if hasattr(finding, 'remediation'):
                print("- Remediation:", finding.remediation)
    
    assert result is True
    assert len(findings) == 0
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
