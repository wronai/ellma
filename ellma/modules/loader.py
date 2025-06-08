"""
ELLMa Dynamic Module Loader

This module handles the dynamic loading, hot-reloading, and dependency management
of ELLMa modules with safety checks and performance optimization.
"""

import os
import sys
import ast
import importlib
import importlib.util
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Set
from datetime import datetime
import traceback
import weakref

from ellma.utils.logger import get_logger

logger = get_logger(__name__)


class ModuleDependency:
    """Represents a module dependency"""

    def __init__(self, name: str, version: Optional[str] = None,
                 import_path: Optional[str] = None):
        self.name = name
        self.version = version
        self.import_path = import_path
        self.satisfied = False
        self.error = None


class ModuleLoadError(Exception):
    """Exception raised when module loading fails"""
    pass


class ModuleLoader:
    """
    Dynamic Module Loader for ELLMa

    Handles loading, reloading, and dependency management of modules
    with safety checks and performance optimization.
    """

    def __init__(self, agent=None):
        """Initialize Module Loader"""
        self.agent = agent
        self.loaded_modules: Dict[str, Any] = {}
        self.module_specs: Dict[str, importlib.util.ModuleSpec] = {}
        self.module_sources: Dict[str, str] = {}  # module_name -> file_path
        self.module_dependencies: Dict[str, List[ModuleDependency]] = {}
        self.module_timestamps: Dict[str, float] = {}
        self.loading_lock = threading.RLock()
        self.watchers: Dict[str, 'FileWatcher'] = {}
        self.auto_reload = False

        # Module safety settings
        self.max_load_time = 30.0  # seconds
        self.allowed_imports = {
            'os', 'sys', 'json', 're', 'time', 'datetime', 'pathlib',
            'requests', 'typing', 'functools', 'itertools', 'collections',
            'logging', 'subprocess', 'shutil', 'tempfile', 'hashlib',
            'base64', 'urllib', 'http', 'email', 'csv', 'xml', 'sqlite3'
        }
        self.blocked_imports = {
            'eval', 'exec', 'compile', '__import__', 'globals', 'locals'
        }

    def load_module(self, module_path: Path, module_name: Optional[str] = None) -> Optional[Any]:
        """
        Load a module from file path

        Args:
            module_path: Path to module file
            module_name: Optional module name (defaults to filename)

        Returns:
            Loaded module instance or None if failed
        """
        module_path = Path(module_path).resolve()

        if not module_path.exists():
            raise ModuleLoadError(f"Module file not found: {module_path}")

        if module_name is None:
            module_name = module_path.stem

        with self.loading_lock:
            try:
                # Check if module is already loaded and up to date
                if self._is_module_current(module_name, module_path):
                    logger.debug(f"Module {module_name} is current, returning cached version")
                    return self.loaded_modules.get(module_name)

                # Validate module before loading
                validation_result = self._validate_module(module_path)
                if not validation_result['valid']:
                    raise ModuleLoadError(f"Module validation failed: {validation_result['errors']}")

                # Load module spec
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None or spec.loader is None:
                    raise ModuleLoadError(f"Cannot create module spec for {module_path}")

                # Create module
                module = importlib.util.module_from_spec(spec)

                # Store in sys.modules temporarily for import resolution
                old_module = sys.modules.get(module_name)
                sys.modules[module_name] = module

                try:
                    # Execute module with timeout
                    start_time = time.time()
                    spec.loader.exec_module(module)
                    load_time = time.time() - start_time

                    if load_time > self.max_load_time:
                        logger.warning(f"Module {module_name} took {load_time:.2f}s to load")

                    # Validate loaded module
                    module_instance = self._create_module_instance(module, module_name)
                    if module_instance is None:
                        raise ModuleLoadError(f"No valid module class found in {module_path}")

                    # Store module information
                    self.loaded_modules[module_name] = module_instance
                    self.module_specs[module_name] = spec
                    self.module_sources[module_name] = str(module_path)
                    self.module_timestamps[module_name] = module_path.stat().st_mtime

                    # Setup file watcher if auto-reload is enabled
                    if self.auto_reload:
                        self._setup_file_watcher(module_name, module_path)

                    logger.info(f"Successfully loaded module: {module_name}")
                    return module_instance

                finally:
                    # Restore original module or remove from sys.modules
                    if old_module is not None:
                        sys.modules[module_name] = old_module
                    else:
                        sys.modules.pop(module_name, None)

            except Exception as e:
                logger.error(f"Failed to load module {module_name}: {e}")
                logger.debug(traceback.format_exc())
                raise ModuleLoadError(f"Module loading failed: {e}")

    def reload_module(self, module_name: str) -> Optional[Any]:
        """
        Reload a module

        Args:
            module_name: Name of module to reload

        Returns:
            Reloaded module instance
        """
        with self.loading_lock:
            if module_name not in self.module_sources:
                raise ModuleLoadError(f"Module {module_name} not found for reload")

            # Unload current module
            self.unload_module(module_name)

            # Reload from source
            module_path = Path(self.module_sources[module_name])
            return self.load_module(module_path, module_name)

    def unload_module(self, module_name: str) -> bool:
        """
        Unload a module

        Args:
            module_name: Name of module to unload

        Returns:
            True if successful
        """
        with self.loading_lock:
            try:
                # Call cleanup if available
                if module_name in self.loaded_modules:
                    module_instance = self.loaded_modules[module_name]
                    if hasattr(module_instance, 'cleanup'):
                        try:
                            module_instance.cleanup()
                        except Exception as e:
                            logger.warning(f"Error during module cleanup for {module_name}: {e}")

                # Remove from tracking
                self.loaded_modules.pop(module_name, None)
                self.module_specs.pop(module_name, None)
                self.module_timestamps.pop(module_name, None)
                self.module_dependencies.pop(module_name, None)

                # Stop file watcher
                if module_name in self.watchers:
                    self.watchers[module_name].stop()
                    del self.watchers[module_name]

                # Remove from sys.modules if present
                if module_name in sys.modules:
                    del sys.modules[module_name]

                logger.info(f"Successfully unloaded module: {module_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to unload module {module_name}: {e}")
                return False

    def load_modules_from_directory(self, directory: Path, recursive: bool = True) -> Dict[str, Any]:
        """
        Load all modules from a directory

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories

        Returns:
            Dictionary of loaded modules
        """
        directory = Path(directory)
        loaded = {}

        if not directory.exists():
            logger.warning(f"Module directory not found: {directory}")
            return loaded

        # Find Python files
        if recursive:
            python_files = directory.rglob("*.py")
        else:
            python_files = directory.glob("*.py")

        for file_path in python_files:
            # Skip __init__.py and files starting with _
            if file_path.name.startswith('_'):
                continue

            module_name = file_path.stem

            try:
                module_instance = self.load_module(file_path, module_name)
                if module_instance:
                    loaded[module_name] = module_instance

            except ModuleLoadError as e:
                logger.error(f"Failed to load module {file_path}: {e}")
                continue

        logger.info(f"Loaded {len(loaded)} modules from {directory}")
        return loaded

    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded module"""
        if module_name not in self.loaded_modules:
            return None

        module_instance = self.loaded_modules[module_name]
        source_path = self.module_sources.get(module_name, "unknown")

        return {
            'name': module_name,
            'source_path': source_path,
            'class_name': module_instance.__class__.__name__,
            'loaded_at': self.module_timestamps.get(module_name),
            'has_cleanup': hasattr(module_instance, 'cleanup'),
            'dependencies': self.module_dependencies.get(module_name, []),
            'auto_reload': module_name in self.watchers
        }

    def list_loaded_modules(self) -> List[str]:
        """Get list of loaded module names"""
        return list(self.loaded_modules.keys())

    def enable_auto_reload(self, enable: bool = True):
        """Enable or disable automatic module reloading"""
        self.auto_reload = enable

        if enable:
            # Setup watchers for already loaded modules
            for module_name, source_path in self.module_sources.items():
                if module_name not in self.watchers:
                    self._setup_file_watcher(module_name, Path(source_path))
        else:
            # Stop all watchers
            for watcher in self.watchers.values():
                watcher.stop()
            self.watchers.clear()

    def _validate_module(self, module_path: Path) -> Dict[str, Any]:
        """Validate module before loading"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Read and parse module
            with open(module_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=str(module_path))

            # Check for security issues
            security_check = self._check_security(tree)
            if security_check['issues']:
                validation['errors'].extend(security_check['issues'])
                validation['valid'] = False

            # Check for required elements
            structure_check = self._check_module_structure(tree)
            if structure_check['warnings']:
                validation['warnings'].extend(structure_check['warnings'])

        except SyntaxError as e:
            validation['valid'] = False
            validation['errors'].append(f"Syntax error: {e}")
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {e}")

        return validation

    def _check_security(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Check for security issues in module AST"""
        issues = []

        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.blocked_imports:
                        issues.append(f"Blocked function call: {node.func.id}")

            # Check imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_imports:
                        issues.append(f"Potentially unsafe import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.allowed_imports:
                    issues.append(f"Potentially unsafe import: {node.module}")

        return {'issues': issues}

    def _check_module_structure(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Check module structure for ELLMa compatibility"""
        warnings = []

        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        if not classes:
            warnings.append("No classes found - module may not be ELLMa compatible")

        # Look for ELLMa module patterns
        has_init = False
        has_commands = False

        for cls in classes:
            # Check for __init__ method
            for node in cls.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name == '__init__':
                        has_init = True
                    elif node.name == 'get_commands':
                        has_commands = True

        if not has_init:
            warnings.append("No __init__ method found in classes")

        if not has_commands:
            warnings.append("No get_commands method found - may not integrate properly")

        return {'warnings': warnings}

    def _create_module_instance(self, module, module_name: str) -> Optional[Any]:
        """Create instance from loaded module"""
        # Look for module classes
        module_classes = []

        for name in dir(module):
            obj = getattr(module, name)

            if (isinstance(obj, type) and
                    not name.startswith('_') and
                    hasattr(obj, '__init__')):
                module_classes.append(obj)

        if not module_classes:
            return None

        # Try to find the best class
        best_class = None

        # Prefer classes with ELLMa patterns
        for cls in module_classes:
            if (hasattr(cls, 'get_commands') or
                    cls.__name__.endswith('Commands') or
                    cls.__name__.endswith('Module')):
                best_class = cls
                break

        # Fallback to first class
        if best_class is None:
            best_class = module_classes[0]

        try:
            # Try to create instance with agent
            if self.agent:
                return best_class(self.agent)
            else:
                return best_class()

        except TypeError:
            # Try without arguments
            try:
                return best_class()
            except Exception as e:
                logger.error(f"Failed to instantiate {best_class.__name__}: {e}")
                return None

    def _is_module_current(self, module_name: str, module_path: Path) -> bool:
        """Check if module is current (not modified since load)"""
        if module_name not in self.loaded_modules:
            return False

        if module_name not in self.module_timestamps:
            return False

        try:
            current_mtime = module_path.stat().st_mtime
            stored_mtime = self.module_timestamps[module_name]
            return abs(current_mtime - stored_mtime) < 1.0  # 1 second tolerance
        except OSError:
            return False

    def _setup_file_watcher(self, module_name: str, module_path: Path):
        """Setup file watcher for automatic reloading"""
        if module_name in self.watchers:
            return

        watcher = FileWatcher(
            module_path,
            lambda: self._on_file_changed(module_name)
        )
        watcher.start()
        self.watchers[module_name] = watcher

    def _on_file_changed(self, module_name: str):
        """Handle file change event"""
        logger.info(f"File changed for module {module_name}, reloading...")

        try:
            self.reload_module(module_name)
            logger.info(f"Successfully reloaded module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to reload module {module_name}: {e}")

    def cleanup(self):
        """Cleanup loader and unload all modules"""
        logger.info("Cleaning up module loader")

        # Stop all watchers
        for watcher in self.watchers.values():
            watcher.stop()
        self.watchers.clear()

        # Unload all modules
        for module_name in list(self.loaded_modules.keys()):
            self.unload_module(module_name)


class FileWatcher:
    """Simple file watcher for module auto-reloading"""

    def __init__(self, file_path: Path, callback: callable):
        self.file_path = file_path
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_mtime = None

    def start(self):
        """Start watching file"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop watching file"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _watch_loop(self):
        """Main watching loop"""
        try:
            self.last_mtime = self.file_path.stat().st_mtime
        except OSError:
            return

        while self.running:
            try:
                current_mtime = self.file_path.stat().st_mtime

                if abs(current_mtime - self.last_mtime) > 1.0:  # 1 second threshold
                    self.last_mtime = current_mtime
                    self.callback()

                time.sleep(1.0)  # Check every second

            except OSError:
                # File might be deleted or inaccessible
                break
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                break


# Global loader instance
_loader = None


def get_loader(agent=None) -> ModuleLoader:
    """Get global module loader instance"""
    global _loader
    if _loader is None:
        _loader = ModuleLoader(agent)
    return _loader


if __name__ == "__main__":
    # Test the module loader
    loader = ModuleLoader()

    # Create a test module
    import tempfile

    test_module_code = '''
class TestModule:
    def __init__(self, agent=None):
        self.agent = agent
        self.name = "test"

    def get_commands(self):
        return {"test": self}

    def hello(self):
        return "Hello from test module!"

    def cleanup(self):
        print("Cleaning up test module")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_module_code)
        temp_path = f.name

    try:
        # Test loading
        module = loader.load_module(Path(temp_path), "test_module")
        print(f"Loaded module: {module}")

        # Test module info
        info = loader.get_module_info("test_module")
        print(f"Module info: {info}")

        # Test unloading
        success = loader.unload_module("test_module")
        print(f"Unloaded: {success}")

    finally:
        # Cleanup
        import os

        os.unlink(temp_path)
        loader.cleanup()

    print("Module loader test completed")