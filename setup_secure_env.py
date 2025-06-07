#!/usr/bin/env python3
"""
Setup Script for Secure ELLMa Environment

This script sets up a secure execution environment for ELLMa by:
1. Creating a virtual environment
2. Installing required dependencies
3. Adding dependency checking to all Python files
4. Setting up pre-commit hooks
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Required Python version
REQUIRED_PYTHON = (3, 8)

# Required system dependencies
REQUIRED_SYSTEM_DEPS = ['git', 'python3-venv']

# Required Python packages for development
REQUIRED_DEV_PACKAGES = [
    'pytest>=6.0.0',
    'pytest-cov>=2.0.0',
    'pytest-mock>=3.0.0',
    'black>=21.0',
    'flake8>=3.9.0',
    'mypy>=0.900',
    'pre-commit>=2.0.0',
    'pip-tools>=6.0.0',
]

# Required runtime packages
REQUIRED_RUNTIME_PACKAGES = [
    'rich>=10.0.0',
    'click>=8.0.0',
    'pyyaml>=6.0',
    'requests>=2.25.0',
    'psutil>=5.9.0',
    'numpy>=1.20.0',
    'prompt-toolkit>=3.0.0',
    'SpeechRecognition>=3.8.0',
    'pyttsx3>=2.90',
]

class SetupError(Exception):
    """Custom exception for setup errors."""
    pass

def check_python_version() -> None:
    """Check if the Python version is supported."""
    if sys.version_info < REQUIRED_PYTHON:
        raise SetupError(
            f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ is required. "
            f"You have Python {sys.version_info.major}.{sys.version_info.minor}."
        )

def check_system_dependencies() -> None:
    """Check if required system dependencies are installed."""
    missing = []
    for dep in REQUIRED_SYSTEM_DEPS:
        if not shutil.which(dep):
            missing.append(dep)
    
    if missing:
        raise SetupError(
            f"The following system dependencies are missing: {', '.join(missing)}\n"
            "Please install them using your system package manager."
        )

def create_virtualenv(venv_path: Path) -> None:
    """Create a Python virtual environment."""
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return
    
    print(f"Creating virtual environment at {venv_path}...")
    subprocess.check_call([sys.executable, '-m', 'venv', str(venv_path)])

def install_packages(venv_path: Path) -> None:
    """Install required Python packages in the virtual environment."""
    pip = venv_path / 'bin' / 'pip'
    if sys.platform == 'win32':
        pip = venv_path / 'Scripts' / 'pip.exe'
    
    print("Installing development packages...")
    subprocess.check_call([str(pip), 'install', '-e', '.[dev]'])
    
    print("Installing runtime packages...")
    subprocess.check_call([str(pip), 'install'] + REQUIRED_RUNTIME_PACKAGES)

def setup_pre_commit_hooks() -> None:
    """Set up pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    try:
        subprocess.check_call(['pre-commit', 'install'])
        subprocess.check_call(['pre-commit', 'install', '--hook-type', 'pre-push'])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to set up pre-commit hooks: {e}")

def add_dependency_checking() -> None:
    """Add dependency checking to all Python files."""
    print("Adding dependency checking to Python files...")
    script_path = PROJECT_ROOT / 'scripts' / 'add_dependency_checking.py'
    if not script_path.exists():
        print(f"Warning: Dependency checking script not found at {script_path}")
        return
    
    try:
        subprocess.check_call([sys.executable, str(script_path)])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to add dependency checking: {e}")

def print_success() -> None:
    """Print success message with next steps."""
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print(f"1. Activate the virtual environment:")
    print(f"   source {PROJECT_ROOT}/venv/bin/activate  # Linux/macOS")
    print(f"   {PROJECT_ROOT}\\venv\\Scripts\\activate  # Windows\n")
    print("2. Run the tests:")
    print("   pytest -v")
    print("\n3. Start the secure shell:")
    print(f"   python -m ellma.secure_executor")
    print("\nHappy coding! 🚀")

def main() -> int:
    """Main entry point for the setup script."""
    try:
        print("🚀 Setting up secure ELLMa environment...\n")
        
        # Run setup steps
        check_python_version()
        check_system_dependencies()
        
        venv_path = PROJECT_ROOT / 'venv'
        create_virtualenv(venv_path)
        install_packages(venv_path)
        
        # Add the virtual environment's bin directory to PATH
        venv_bin = str(venv_path / 'bin')
        if sys.platform == 'win32':
            venv_bin = str(venv_path / 'Scripts')
        os.environ['PATH'] = f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"
        
        setup_pre_commit_hooks()
        add_dependency_checking()
        
        print_success()
        return 0
        
    except SetupError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed with exit code {e.returncode}:", file=sys.stderr)
        print(f"   {' '.join(e.cmd) if e.cmd else ''}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
