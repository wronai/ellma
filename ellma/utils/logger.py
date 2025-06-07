"""
ELLMa Logging Utilities

This module provides centralized logging configuration and utilities
for the ELLMa system with rich formatting and multiple output targets.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from rich.logging import RichHandler
from rich.console import Console

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_configured = False

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)

class ELLMaLogFilter(logging.Filter):
    """Custom log filter for ELLMa specific filtering"""

    def __init__(self, module_filter: Optional[str] = None):
        super().__init__()
        self.module_filter = module_filter

    def filter(self, record):
        # Filter sensitive information
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            # Remove potential API keys, passwords, etc.
            sensitive_patterns = ['password', 'token', 'key', 'secret']
            for pattern in sensitive_patterns:
                if pattern in msg.lower():
                    record.msg = msg.replace(msg, '[SENSITIVE DATA FILTERED]')

        # Module-specific filtering
        if self.module_filter and self.module_filter not in record.name:
            return False

        return True

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    rich_console: bool = True,
    max_size: str = "10MB",
    backup_count: int = 5,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup centralized logging for ELLMa

    Args:
        level: Logging level
        log_file: Path to log file
        console: Enable console logging
        rich_console: Use rich console formatting
        max_size: Maximum log file size
        backup_count: Number of backup log files
        format_string: Custom format string

    Returns:
        Configured root logger
    """
    global _configured

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger("ellma")
    root_logger.setLevel(numeric_level)

    # Clear existing handlers if reconfiguring
    if _configured:
        root_logger.handlers.clear()

    # Console handler
    if console:
        if rich_console:
            console_handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True
            )
            console_handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(ColoredFormatter(format_string))

        console_handler.setLevel(numeric_level)
        console_handler.addFilter(ELLMaLogFilter())
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Parse max_size
        size_bytes = _parse_size(max_size)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=size_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        file_handler.addFilter(ELLMaLogFilter())
        root_logger.addHandler(file_handler)

    _configured = True
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Create child logger
    logger = logging.getLogger(f"ellma.{name}")
    _loggers[name] = logger

    # Ensure root logger is configured
    if not _configured:
        setup_logging()

    return logger

def configure_from_config(config: Dict[str, Any]):
    """
    Configure logging from configuration dictionary

    Args:
        config: Logging configuration
    """
    setup_logging(
        level=config.get('level', 'INFO'),
        log_file=config.get('file'),
        console=config.get('console', True),
        max_size=config.get('max_size', '10MB'),
        backup_count=config.get('backup_count', 5)
    )

def _parse_size(size_str: str) -> int:
    """Parse size string to bytes"""
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)

def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise

    return wrapper

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper

class LogContext:
    """Context manager for logging with additional context"""

    def __init__(self, logger: logging.Logger, context: str, level: int = logging.INFO):
        self.logger = logger
        self.context = context
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Starting: {self.context}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.log(self.level, f"Completed: {self.context} ({duration:.3f}s)")
        else:
            self.logger.error(f"Failed: {self.context} ({duration:.3f}s) - {exc_val}")

# Convenience functions for common logging patterns

def log_system_info():
    """Log system information at startup"""
    import platform
    import sys
    import psutil

    logger = get_logger(__name__)

    logger.info("=== ELLMa System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"CPU Count: {psutil.cpu_count()}")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    logger.info("================================")

def log_config_info(config: Dict[str, Any]):
    """Log configuration information"""
    logger = get_logger(__name__)

    logger.info("=== ELLMa Configuration ===")
    logger.info(f"Model: {config.get('model', {}).get('path', 'Not configured')}")
    logger.info(f"Evolution: {'Enabled' if config.get('evolution', {}).get('enabled') else 'Disabled'}")
    logger.info(f"Modules: {config.get('modules', {}).get('custom_path', 'Default')}")
    logger.info("===========================")

def log_performance_metrics(metrics: Dict[str, Any]):
    """Log performance metrics"""
    logger = get_logger(__name__)

    logger.info("=== Performance Metrics ===")
    for key, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.3f}")
        else:
            logger.info(f"{key}: {value}")
    logger.info("===========================")

# Emergency logging for critical errors
def emergency_log(message: str, exc_info=None):
    """Emergency logging that always works"""
    try:
        logger = get_logger("emergency")
        logger.critical(message, exc_info=exc_info)
    except:
        # Fallback to stderr if logging fails
        import traceback
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] EMERGENCY: {message}", file=sys.stderr)
        if exc_info:
            traceback.print_exc(file=sys.stderr)

# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    emergency_log(
        f"Uncaught exception: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

# Install global exception handler
sys.excepthook = handle_exception

if __name__ == "__main__":
    # Test logging setup
    setup_logging(level="DEBUG", console=True, rich_console=True)

    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test performance logging
    @log_performance
    def test_function():
        import time
        time.sleep(0.1)
        return "success"

    test_function()

    # Test context manager
    with LogContext(logger, "test operation"):
        import time
        time.sleep(0.05)

    print("Logging test completed")