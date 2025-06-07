"""
ELLMa Helper Utilities (Legacy)

NOTE: This module is now DEPRECATED and maintained for backward compatibility only.
Please update your imports to use the new modular structure in ellma.utils.helpers.*

Example:
    # Old way (deprecated):
    from ellma.utils.helpers import get_file_hash
    
    # New way (recommended):
    from ellma.utils.helpers.file_utils import get_file_hash
"""

import warnings
from typing import Any, Dict, List, Optional, Union, Callable

# Issue deprecation warning
warnings.warn(
    "The ellma.utils.helpers module is deprecated. "
    "Please import from specific submodules (e.g., ellma.utils.helpers.file_utils).",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all functions from the new module structure
from .helpers.file_utils import (
    ensure_directory,
    get_file_hash,
    get_file_size_human,
    create_temp_file,
    cleanup_temp_files,
    is_newer_than
)

from .helpers.network_utils import (
    is_port_open,
    wait_for_port,
    get_free_port
)

from .helpers.decorators import (
    timeout_decorator,
    retry_decorator,
    memoize_decorator,
    debounce,
    throttle
)

from .helpers.data_utils import (
    deep_merge_dicts,
    flatten_dict,
    chunk_list,
    snake_to_camel,
    camel_to_snake,
    parse_size_string
)

from .helpers.validation import (
    validate_email,
    validate_url,
    validate_ip_address,
    validate_regex,
    validate_file_exists,
    validate_directory,
    validate_type
)

from .helpers.time_utils import (
    get_timestamp,
    parse_timestamp,
    days_ago,
    format_duration,
    time_since,
    is_weekday
)

from .helpers.concurrency import (
    RateLimiter,
    CircuitBreaker,
    TaskPool
)

# Maintain the same interface for backward compatibility
__all__ = [
    # File utilities
    'ensure_directory',
    'get_file_hash',
    'get_file_size_human',
    'create_temp_file',
    'cleanup_temp_files',
    'is_newer_than',
    
    # Network utilities
    'is_port_open',
    'wait_for_port',
    'get_free_port',
    
    # Decorators
    'timeout_decorator',
    'retry_decorator',
    'memoize_decorator',
    'debounce',
    'throttle',
    
    # Data utilities
    'deep_merge_dicts',
    'flatten_dict',
    'chunk_list',
    'snake_to_camel',
    'camel_to_snake',
    'parse_size_string',
    
    # Validation
    'validate_email',
    'validate_url',
    'validate_ip_address',
    'validate_regex',
    'validate_file_exists',
    'validate_directory',
    'validate_type',
    
    # Time utilities
    'get_timestamp',
    'parse_timestamp',
    'days_ago',
    'format_duration',
    'time_since',
    'is_weekday',
    
    # Concurrency
    'RateLimiter',
    'CircuitBreaker',
    'TaskPool'
]

# Keep the safe_import function as it's used by other modules
def safe_import(module_name: str, package: Optional[str] = None):
    """
    Safely import a module, returning None if import fails

    Args:
        module_name: Name of module to import
        package: Package name for relative imports

    Returns:
        Imported module or None if failed
    """
    import importlib
    try:
        return importlib.import_module(module_name, package=package)
    except ImportError:
        import sys
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to import {module_name}")
        return None


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file contents

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)

    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def get_file_size_human(size_bytes: int) -> str:
    """
    Convert bytes to human readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def timeout_decorator(seconds: int, default_return=None):
    """
    Decorator to add timeout to function execution

    Args:
        seconds: Timeout in seconds
        default_return: Value to return on timeout
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

            # Set timeout (Unix only)
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

            except AttributeError:
                # Windows doesn't support SIGALRM
                return func(*args, **kwargs)
            except TimeoutError:
                logger.warning(f"Function {func.__name__} timed out")
                return default_return

        return wrapper

    return decorator


def retry_decorator(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function execution on failure

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier for delay
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    logger.warning(f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def memoize_decorator(ttl_seconds: Optional[int] = None):
    """
    Decorator to memoize function results with optional TTL

    Args:
        ttl_seconds: Time to live for cached results
    """

    def decorator(func):
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))

            # Check if result is cached and not expired
            if key in cache:
                result, timestamp = cache[key]
                if ttl_seconds is None or time.time() - timestamp < ttl_seconds:
                    return result
                else:
                    del cache[key]

            # Calculate and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())

            return result

        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'keys': list(cache.keys())
        }

        return wrapper

    return decorator


def run_command(command: Union[str, List[str]],
                cwd: Optional[str] = None,
                timeout: Optional[int] = 30,
                capture_output: bool = True,
                check: bool = True) -> subprocess.CompletedProcess:
    """
    Run system command with proper error handling

    Args:
        command: Command to run
        cwd: Working directory
        timeout: Command timeout
        capture_output: Capture stdout/stderr
        check: Raise exception on non-zero exit

    Returns:
        CompletedProcess object
    """
    logger.debug(f"Running command: {command}")

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=check,
            shell=isinstance(command, str)
        )

        logger.debug(f"Command completed with exit code: {result.returncode}")
        return result

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {command}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}: {command}")
        if capture_output:
            logger.error(f"Error output: {e.stderr}")
        raise


def find_executable(name: str) -> Optional[str]:
    """
    Find executable in PATH

    Args:
        name: Executable name

    Returns:
        Full path to executable or None if not found
    """
    import shutil
    return shutil.which(name)


def is_port_open(host: str, port: int, timeout: float = 5.0) -> bool:
    """
    Check if a port is open on a host

    Args:
        host: Host to check
        port: Port number
        timeout: Connection timeout

    Returns:
        True if port is open
    """
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False


def wait_for_port(host: str, port: int, timeout: int = 60, interval: float = 1.0) -> bool:
    """
    Wait for a port to become available

    Args:
        host: Host to check
        port: Port number
        timeout: Maximum wait time
        interval: Check interval

    Returns:
        True if port became available
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(interval)

    return False


def get_free_port() -> int:
    """
    Get a free port number

    Returns:
        Available port number
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]

    return port


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten nested dictionary

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Key separator

    Returns:
        Flattened dictionary
    """
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks of specified size

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def debounce(wait_seconds: float):
    """
    Debounce decorator - only execute function after specified delay

    Args:
        wait_seconds: Delay in seconds
    """

    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            if current_time - last_called[0] >= wait_seconds:
                last_called[0] = current_time
                return func(*args, **kwargs)

        return wrapper

    return decorator


def throttle(rate_limit: float):
    """
    Throttle decorator - limit function execution rate

    Args:
        rate_limit: Minimum seconds between calls
    """

    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            elapsed = current_time - last_called[0]

            if elapsed < rate_limit:
                time.sleep(rate_limit - elapsed)

            last_called[0] = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def create_temp_file(suffix: str = '', prefix: str = 'ellma_', content: str = '') -> str:
    """
    Create temporary file with content

    Args:
        suffix: File suffix
        prefix: File prefix
        content: File content

    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=prefix, delete=False) as f:
        f.write(content)
        return f.name


def cleanup_temp_files(pattern: str = 'ellma_*'):
    """
    Clean up temporary files matching pattern

    Args:
        pattern: File pattern to match
    """
    import glob
    temp_dir = tempfile.gettempdir()

    for file_path in glob.glob(os.path.join(temp_dir, pattern)):
        try:
            os.unlink(file_path)
            logger.debug(f"Cleaned up temp file: {file_path}")
        except OSError as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {e}")


def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def parse_size_string(size_str: str) -> int:
    """
    Parse size string to bytes

    Args:
        size_str: Size string like "10MB", "1.5GB"

    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()

    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        'PB': 1024 ** 5
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number_part = size_str[:-len(suffix)]
            return int(float(number_part) * multiplier)

    # No suffix, assume bytes
    return int(size_str)


def validate_email(email: str) -> bool:
    """
    Simple email validation

    Args:
        email: Email address to validate

    Returns:
        True if email appears valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Simple URL validation

    Args:
        url: URL to validate

    Returns:
        True if URL appears valid
    """
    import re
    pattern = r'^https?://[^\s/$.?#]+\.[^\s]*$'
    return re.match(pattern, url) is not None


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate string to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case to camelCase

    Args:
        snake_str: Snake case string

    Returns:
        Camel case string
    """
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase to snake_case

    Args:
        camel_str: Camel case string

    Returns:
        Snake case string
    """
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_system_info() -> Dict[str, Any]:
    """
    Get basic system information

    Returns:
        Dictionary with system information
    """
    import platform
    import psutil

    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'disk_total': psutil.disk_usage('/').total,
        'hostname': platform.node(),
        'username': os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    }


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings

    Args:
        version1: First version
        version2: Second version

    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """

    def normalize_version(v):
        parts = [int(x) for x in v.split('.')]
        # Pad with zeros to make same length
        while len(parts) < 3:
            parts.append(0)
        return parts

    v1_parts = normalize_version(version1)
    v2_parts = normalize_version(version2)

    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = v1_parts[i] if i < len(v1_parts) else 0
        v2_part = v2_parts[i] if i < len(v2_parts) else 0

        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1

    return 0


def get_git_info(repo_path: str = '.') -> Dict[str, str]:
    """
    Get Git repository information

    Args:
        repo_path: Path to Git repository

    Returns:
        Dictionary with Git information
    """
    git_info = {}

    try:
        # Get current branch
        result = run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path)
        git_info['branch'] = result.stdout.strip()

        # Get current commit hash
        result = run_command(['git', 'rev-parse', 'HEAD'], cwd=repo_path)
        git_info['commit'] = result.stdout.strip()

        # Get commit message
        result = run_command(['git', 'log', '-1', '--pretty=%B'], cwd=repo_path)
        git_info['message'] = result.stdout.strip()

        # Get author
        result = run_command(['git', 'log', '-1', '--pretty=%an'], cwd=repo_path)
        git_info['author'] = result.stdout.strip()

        # Get commit date
        result = run_command(['git', 'log', '-1', '--pretty=%ci'], cwd=repo_path)
        git_info['date'] = result.stdout.strip()

        # Check if working directory is clean
        result = run_command(['git', 'status', '--porcelain'], cwd=repo_path)
        git_info['clean'] = len(result.stdout.strip()) == 0

    except subprocess.CalledProcessError:
        git_info['error'] = 'Not a git repository or git not available'

    return git_info


def create_progress_bar(total: int, width: int = 50) -> Callable:
    """
    Create a simple progress bar function

    Args:
        total: Total number of items
        width: Width of progress bar

    Returns:
        Function to update progress
    """

    def update_progress(current: int, message: str = ''):
        if total == 0:
            percent = 100
        else:
            percent = min(100, (current * 100) // total)

        filled = (percent * width) // 100
        bar = '█' * filled + '░' * (width - filled)

        print(f'\r{bar} {percent:3d}% {message}', end='', flush=True)

        if current >= total:
            print()  # New line when complete

    return update_progress


def singleton(cls):
    """
    Singleton decorator for classes

    Args:
        cls: Class to make singleton

    Returns:
        Singleton class
    """
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class ContextTimer:
    """Context manager for timing operations"""

    def __init__(self, name: str = 'Operation'):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.name} took {format_duration(duration)}")

    @property
    def elapsed(self) -> float:
        """Get elapsed time"""
        if self.start_time is None:
            return 0

        end = self.end_time if self.end_time else time.time()
        return end - self.start_time


class RateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def acquire(self) -> bool:
        """
        Try to acquire permission for a call

        Returns:
            True if call is allowed
        """
        current_time = time.time()

        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls
                      if current_time - call_time < self.time_window]

        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(current_time)
            return True

        return False

    def wait_time(self) -> float:
        """
        Get time to wait before next call is allowed

        Returns:
            Wait time in seconds
        """
        if len(self.calls) < self.max_calls:
            return 0

        current_time = time.time()
        oldest_call = min(self.calls)

        return max(0, self.time_window - (current_time - oldest_call))


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """
        Call function with circuit breaker protection

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset circuit breaker"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.recovery_timeout)

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'CLOSED'

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


# Utility functions for common tasks
def get_timestamp(format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> datetime:
    """Parse timestamp string to datetime"""
    return datetime.strptime(timestamp_str, format_str)


def days_ago(days: int) -> datetime:
    """Get datetime object for N days ago"""
    return datetime.now() - timedelta(days=days)


def is_newer_than(file_path: Union[str, Path], hours: int) -> bool:
    """Check if file is newer than specified hours"""
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    cutoff_time = datetime.now() - timedelta(hours=hours)

    return file_time > cutoff_time


if __name__ == "__main__":
    # Test helper functions
    print("Testing ELLMa helper functions...")

    # Test file operations
    temp_file = create_temp_file(content="Test content")
    print(f"Created temp file: {temp_file}")

    file_hash = get_file_hash(temp_file)
    print(f"File hash: {file_hash}")

    # Test timing
    with ContextTimer("Test operation"):
        time.sleep(0.1)

    # Test rate limiter
    limiter = RateLimiter(max_calls=3, time_window=1.0)
    for i in range(5):
        if limiter.acquire():
            print(f"Call {i + 1} allowed")
        else:
            print(f"Call {i + 1} blocked, wait {limiter.wait_time():.2f}s")

    # Cleanup
    cleanup_temp_files()
    print("Helper functions test completed")