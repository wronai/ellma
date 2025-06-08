#!/usr/bin/env python3
"""
Dependency Checker for ELLMa

This script checks for missing or outdated dependencies and ensures the
environment is properly configured. It's designed to be run as a pre-commit hook
and as part of the CI/CD pipeline.
"""

import argparse
import importlib
import json
import logging
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dependency_check.log"),
    ],
)
logger = logging.getLogger("dependency_checker")

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class Dependency(NamedTuple):
    """Represents a Python package dependency."""
    name: str
    required_version: Optional[str] = None
    required: bool = True


class DependencyCheckResult(NamedTuple):
    """Result of a dependency check."""
    success: bool
    message: str
    dependency: Dependency
    installed_version: Optional[str] = None


def get_installed_version(package_name: str) -> Optional[str]:
    """Get the installed version of a package."""
    try:
        if package_name == "python":
            return ".".join(map(str, sys.version_info[:3]))
            
        module = importlib.import_module(package_name.replace("-", "_"))
        if hasattr(module, "__version__"):
            return str(module.__version__)
        elif hasattr(module, "version"):
            return str(module.version)
        elif hasattr(module, "VERSION"):
            return str(module.VERSION)
    except ImportError:
        pass
    return None


def check_dependency(dep: Dependency) -> DependencyCheckResult:
    """Check if a dependency is installed and meets version requirements."""
    installed_version = get_installed_version(dep.name)
    
    if installed_version is None:
        if dep.required:
            return DependencyCheckResult(
                False,
                f"Required dependency '{dep.name}' is not installed",
                dep,
            )
        return DependencyCheckResult(
            True, f"Optional dependency '{dep.name}' is not installed", dep
        )
    
    if dep.required_version:
        # Simple version comparison (for demo purposes)
        # In a real-world scenario, use packaging.version.parse
        required_parts = dep.required_version.split(".")
        installed_parts = installed_version.split(".")
        
        for req, inst in zip(required_parts, installed_parts):
            if inst < req:
                return DependencyCheckResult(
                    False,
                    f"Dependency '{dep.name}' version {inst} is older than required {dep.required_version}",
                    dep,
                    installed_version,
                )
    
    return DependencyCheckResult(
        True,
        f"Dependency '{dep.name}' is installed (version {installed_version})",
        dep,
        installed_version,
    )


def check_poetry_environment() -> Tuple[bool, str]:
    """Check if Poetry environment is properly set up."""
    try:
        result = subprocess.run(
            ["poetry", "check"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            return False, f"Poetry check failed: {result.stderr}"
        return True, "Poetry environment is valid"
    except FileNotFoundError:
        return False, "Poetry is not installed"


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements."""
    required = (3, 8)
    current = sys.version_info[:2]
    if current < required:
        return (
            False,
            f"Python {current[0]}.{current[1]} is not supported. "
            f"Please upgrade to Python {required[0]}.{required[1]} or higher.",
        )
    return True, f"Python {current[0]}.{current[1]} is supported"


def check_environment() -> Dict[str, Tuple[bool, str]]:
    """Check the development environment."""
    checks = {
        "python_version": check_python_version(),
        "poetry_environment": check_poetry_environment(),
    }
    return checks


def check_dependencies(dependencies: List[Dependency]) -> List[DependencyCheckResult]:
    """Check a list of dependencies."""
    return [check_dependency(dep) for dep in dependencies]


def print_check_result(result: Tuple[bool, str], prefix: str = "  - ") -> None:
    """Print the result of a check."""
    success, message = result
    status = "✅" if success else "❌"
    print(f"{prefix}{status} {message}")


def print_dependency_result(result: DependencyCheckResult) -> None:
    """Print the result of a dependency check."""
    status = "✅" if result.success else "❌"
    version_info = f" (installed: {result.installed_version})" if result.installed_version else ""
    print(f"  {status} {result.dependency.name}{version_info}")
    if not result.success:
        print(f"    ⚠️  {result.message}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check project dependencies")
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

    print("🔍 Checking development environment...")
    env_checks = check_environment()
    
    all_checks_passed = True
    for name, check in env_checks.items():
        print_check_result(check, prefix=f"  - {name.replace('_', ' ').title()}: ")
        all_checks_passed = all_checks_passed and check[0]

    if not all_checks_passed:
        print("\n❌ Some environment checks failed. Please fix them and try again.")
        return 1

    print("\n🔍 Checking dependencies...")
    
    # Load dependencies from pyproject.toml (simplified for demo)
    dependencies = [
        Dependency("python", "3.8.0"),
        Dependency("poetry", "1.2.0"),
        Dependency("black", "22.8.0"),
        Dependency("flake8", "5.0.0"),
        Dependency("mypy", "0.991"),
        Dependency("pytest", "7.0.0"),
    ]
    
    results = check_dependencies(dependencies)
    
    all_deps_ok = True
    for result in results:
        print_dependency_result(result)
        all_deps_ok = all_deps_ok and result.success
    
    if not all_deps_ok:
        print("\n❌ Some dependencies are missing or outdated.")
        if args.fix:
            print("\n🔄 Attempting to fix dependencies...")
            try:
                subprocess.check_call(["poetry", "install"], cwd=PROJECT_ROOT)
                print("✅ Dependencies updated successfully!")
                return 0
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to update dependencies: {e}")
                return 1
        else:
            print("\n💡 Run with --fix to automatically install missing dependencies.")
        return 1
    
    print("\n✅ All dependencies are up to date!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
