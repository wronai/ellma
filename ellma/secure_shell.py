"""
Secure Shell Wrapper for ELLMa

This module provides a secure entry point for the ELLMa application that ensures
all security and dependency checks are performed before the main application runs.
"""

import os
import sys
import logging
import argparse
from typing import Optional, List
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ellma.secure_shell')

def setup_environment() -> bool:
    """Set up the environment and check dependencies."""
    try:
        # Import security module
        from ellma.security import ensure_environment, EnvironmentStatus
        
        # Run environment checks and auto-repair
        if not ensure_environment(auto_repair=True):
            logger.error("Failed to set up environment. See logs for details.")
            return False
            
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import security module: {e}")
        logger.error("This suggests a critical installation issue.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during environment setup: {e}", exc_info=True)
        return False

def run_shell():
    """Run the ELLMa interactive shell."""
    try:
        from ellma.cli.shell import interactive_shell
        interactive_shell()
    except ImportError as e:
        logger.error(f"Failed to import interactive shell: {e}")
        return False
    except Exception as e:
        logger.error(f"Error in interactive shell: {e}", exc_info=True)
        return False
    return True

def run_command(command: str, args: Optional[List[str]] = None) -> bool:
    """Run a single ELLMa command."""
    try:
        from ellma.cli.main import cli
        
        # Reconstruct command line arguments
        cmd_args = [command]
        if args:
            cmd_args.extend(args)
            
        # Save original sys.argv
        original_argv = sys.argv
        sys.argv = [sys.argv[0]] + cmd_args
        
        try:
            cli()
            return True
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
            
    except ImportError as e:
        logger.error(f"Failed to import CLI module: {e}")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}", exc_info=True)
        return False

def main():
    """Main entry point for the secure shell."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='ELLMa Secure Shell')
    parser.add_argument('command', nargs='?', help='Command to run (optional)')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up environment
    if not setup_environment():
        sys.exit(1)
    
    # Run the requested command or start interactive shell
    if args.command:
        success = run_command(args.command, args.args)
        sys.exit(0 if success else 1)
    else:
        success = run_shell()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
