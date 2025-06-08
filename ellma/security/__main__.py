"""
Main entry point for the security module.
This module is executed before any other code to ensure the environment is properly set up.
"""

import os
import sys
import logging
from typing import Optional
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ellma.security')

def run_security_checks():
    """Run security and environment checks before importing any other modules."""
    try:
        from .core import env_manager, EnvironmentStatus
        
        # Check environment
        check = env_manager.check_environment()
        
        if check.status != EnvironmentStatus.VALID:
            logger.warning(f"Environment issue detected: {check.error}")
            
            # Try to fix issues automatically
            if not env_manager.ensure_environment(auto_repair=True):
                logger.error("Failed to automatically fix environment issues.")
                if check.status == EnvironmentStatus.NOT_IN_VENV:
                    logger.error(
                        "Please activate a virtual environment first. "
                        "You can create one with: python -m venv .venv"
                    )
                return False
        
        logger.info("Environment checks passed")
        return True
        
    except Exception as e:
        logger.error(f"Error during security checks: {e}", exc_info=True)
        return False

# Run security checks when this module is imported
if not os.environ.get('ELLMA_SKIP_CHECKS'):
    run_security_checks()
