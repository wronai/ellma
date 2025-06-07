"""
Error logging system for ELLMa.

This module provides functionality to log errors with context for later analysis
and system improvement through the evolution process.
"""
import json
import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ErrorLogger:
    """
    A class to handle error logging with context for the ELLMa system.
    """
    
    def __init__(self, log_dir: str = "./TODO"):
        """
        Initialize the error logger.
        
        Args:
            log_dir: Directory to store error logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.log_file = self.log_dir / "errors.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, 'a'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ELLMaErrorLogger")
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> Dict[str, Any]:
        """
        Log an error with context information.
        
        Args:
            error: The exception that was raised
            context: Additional context about the error
            severity: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Dict containing the logged error information
        """
        if context is None:
            context = {}
            
        # Get error information
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "severity": severity,
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        # Log the error
        log_message = {
            "type": "error",
            "data": error_info
        }
        
        self.logger.error(json.dumps(log_message, indent=2))
        
        # Save to a structured error log
        self._save_structured_error(error_info)
        
        return error_info
    
    def _save_structured_error(self, error_info: Dict[str, Any]) -> None:
        """
        Save error information to a structured JSON file.
        
        Args:
            error_info: Dictionary containing error information
        """
        # Create a structured filename with timestamp and error type
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        error_type = error_info["error_type"].lower().replace(" ", "_")
        filename = f"error_{timestamp}_{error_type}.json"
        
        # Save the error information
        error_file = self.log_dir / "errors" / filename
        error_file.parent.mkdir(exist_ok=True)
        
        with open(error_file, 'w') as f:
            json.dump(error_info, f, indent=2)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged errors.
        
        Returns:
            Dictionary containing error statistics
        """
        error_dir = self.log_dir / "errors"
        if not error_dir.exists():
            return {"total_errors": 0, "error_types": {}}
        
        error_files = list(error_dir.glob("error_*.json"))
        error_types = {}
        
        for error_file in error_files:
            try:
                with open(error_file, 'r') as f:
                    error_data = json.load(f)
                    error_type = error_data.get("error_type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            except Exception as e:
                self.logger.error(f"Error reading error file {error_file}: {e}")
        
        return {
            "total_errors": len(error_files),
            "error_types": error_types,
            "last_updated": datetime.utcnow().isoformat()
        }

# Global instance for easy access
error_logger = ErrorLogger()

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, severity: str = "ERROR") -> Dict[str, Any]:
    """
    Log an error using the global error logger.
    
    Args:
        error: The exception that was raised
        context: Additional context about the error
        severity: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Dict containing the logged error information
    """
    return error_logger.log_error(error, context, severity)

def get_error_stats() -> Dict[str, Any]:
    """
    Get statistics about logged errors.
    
    Returns:
        Dictionary containing error statistics
    """
    return error_logger.get_error_stats()
