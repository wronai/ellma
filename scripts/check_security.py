#!/usr/bin/env python3
"""
Security Checker for ELLMa

This script performs security checks on the project, including:
- Scanning for known vulnerabilities in dependencies
- Checking for insecure code patterns
- Verifying security best practices
"""

import argparse
import json
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("security_check.log"),
    ],
)
logger = logging.getLogger("security_checker")

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

class SecurityCheckResult(NamedTuple):
    """Result of a security check."""
    success: bool
    message: str
    details: Optional[Dict] = None

def run_bandit() -> SecurityCheckResult:
    """Run Bandit security linter."""
    try:
        result = subprocess.run(
            ["bandit", "-r", "-f", "json", "-ll", "-iii", "ellma/"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        
        try:
            report = json.loads(result.stdout)
            issues = report.get("results", [])
            
            if issues:
                return SecurityCheckResult(
                    False,
                    f"Found {len(issues)} potential security issues",
                    {"issues": issues, "report": report},
                )
            return SecurityCheckResult(True, "No security issues found by Bandit")
            
        except json.JSONDecodeError:
            return SecurityCheckResult(
                False,
                f"Failed to parse Bandit output: {result.stderr}",
            )
            
    except FileNotFoundError:
        return SecurityCheckResult(
            False, "Bandit is not installed. Install with: pip install bandit"
        )
    except subprocess.CalledProcessError as e:
        return SecurityCheckResult(
            False, f"Bandit check failed: {e.stderr}"
        )

def run_safety_check() -> SecurityCheckResult:
    """Check for known vulnerabilities in dependencies."""
    try:
        result = subprocess.run(
            ["safety", "check", "--json", "--full-report"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        
        if result.returncode != 0:
            try:
                report = json.loads(result.stdout)
                vulnerabilities = report.get("vulnerabilities", [])
                if vulnerabilities:
                    return SecurityCheckResult(
                        False,
                        f"Found {len(vulnerabilities)} vulnerable dependencies",
                        {"vulnerabilities": vulnerabilities},
                    )
            except json.JSONDecodeError:
                return SecurityCheckResult(
                    False,
                    f"Failed to parse safety output: {result.stderr}",
                )
        
        return SecurityCheckResult(True, "No known vulnerabilities found")
        
    except FileNotFoundError:
        return SecurityCheckResult(
            False, "safety is not installed. Install with: pip install safety"
        )

def check_file_permissions() -> SecurityCheckResult:
    """Check for insecure file permissions."""
    sensitive_files = [
        "pyproject.toml",
        "poetry.lock",
        ".env",
        "*.pem",
        "*.key",
        "*.crt",
    ]
    
    issues = []
    for pattern in sensitive_files:
        for file in PROJECT_ROOT.glob(pattern):
            if file.is_file() and file.stat().st_mode & 0o077:
                issues.append(
                    f"Insecure permissions on {file.relative_to(PROJECT_ROOT)}: "
                    f"{oct(file.stat().st_mode & 0o777)}"
                )
    
    if issues:
        return SecurityCheckResult(
            False,
            f"Found {len(issues)} files with insecure permissions",
            {"issues": issues},
        )
    return SecurityCheckResult(True, "No insecure file permissions found")

def check_hardcoded_secrets() -> SecurityCheckResult:
    """Check for hardcoded secrets in the codebase."""
    patterns = [
        r'password\s*[:=]\s*["\'].*?["\']',
        r'api[_-]?key\s*[:=]\s*["\'].*?["\']',
        r'secret[_-]?key\s*[:=]\s*["\'].*?["\']',
        r'token\s*[:=]\s*["\'].*?["\']',
    ]
    
    issues = []
    for py_file in PROJECT_ROOT.rglob("*.py"):
        try:
            content = py_file.read_text()
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(
                        f"Potential hardcoded secret in {py_file.relative_to(PROJECT_ROOT)}"
                    )
                    break  # Only report each file once
        except (UnicodeDecodeError, PermissionError) as e:
            logger.warning(f"Could not read {py_file}: {e}")
    
    if issues:
        return SecurityCheckResult(
            False,
            f"Found {len(issues)} potential hardcoded secrets",
            {"issues": issues},
        )
    return SecurityCheckResult(True, "No hardcoded secrets found")

def run_security_checks() -> Dict[str, SecurityCheckResult]:
    """Run all security checks."""
    return {
        "bandit": run_bandit(),
        "safety": run_safety_check(),
        "file_permissions": check_file_permissions(),
        "hardcoded_secrets": check_hardcoded_secrets(),
    }

def print_check_result(name: str, result: SecurityCheckResult) -> None:
    """Print the result of a security check."""
    status = "✅" if result.success else "❌"
    print(f"{status} {name}: {result.message}")
    
    if not result.success and result.details:
        if "issues" in result.details:
            for issue in result.details["issues"][:3]:  # Show first 3 issues
                print(f"  • {issue}")
            if len(result.details["issues"]) > 3:
                print(f"  ... and {len(result.details['issues']) - 3} more")

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run security checks on the project")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues when possible",
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity"
    )
    args = parser.parse_args()

    # Configure logging verbosity
    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    print("🔒 Running security checks...\n")
    
    results = run_security_checks()
    
    all_checks_passed = True
    for name, result in results.items():
        print_check_result(name.replace("_", " ").title(), result)
        all_checks_passed = all_checks_passed and result.success
    
    if all_checks_passed:
        print("\n✅ All security checks passed!")
        return 0
    else:
        print("\n❌ Some security checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
