"""
ELLMa Module Registry - Dynamic Module Loading and Management

This module handles the registration, loading, and management of ELLMa modules
including built-in modules, custom modules, and dynamically generated modules.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import json
import traceback
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class ModuleMetadata:
    """Metadata for registered modules"""

    def __init__(self, name: str, module_class: Type, source_path: str,
                 description: str = "", version: str = "1.0.0"):
        self.name = name
        self.module_class = module_class
        self.source_path = source_path
        self.description = description
        self.version = version
        self.loaded_at = datetime.now().isoformat()
        self.instance = None
        self.load_count = 0
        self.error_count = 0
        self.last_error = None

class ModuleRegistry:
    """
    Module Registry for ELLMa

    Handles dynamic loading and management of modules including:
    - Built-in command modules
    - Custom user modules
    - Generated modules from evolution
    - Module lifecycle management
    """

    def __init__(self):
        """Initialize Module Registry"""
        self.modules: Dict[str, ModuleMetadata] = {}
        self.module_paths: List[Path] = []
        self.auto_reload = False
        self._watched_files = {}

    def register_module(self, name: str, module_class: Type, source_path: str = "",
                       description: str = "", version: str = "1.0.0") -> bool:
        """
        Register a module class

        Args:
            name: Module name
            module_class: Module class
            source_path: Source file path
            description: Module description
            version: Module version

        Returns:
            True if registration successful
        """
        try:
            # Validate module class
            if not hasattr(module_class, '__init__'):
                logger.error(f"Invalid module class: {module_class}")
                return False

            # Create metadata
            metadata = ModuleMetadata(
                name=name,
                module_class=module_class,
                source_path=source_path,
                description=description,
                version=version
            )

            self.modules[name] = metadata
            logger.info(f"Registered module: {name} (version: {version})")
            return True

        except Exception as e:
            logger.error(f"Failed to register module {name}: {e}")
            return False

    def load_module(self, name: str, agent=None) -> Optional[Any]:
        """
        Load and instantiate a module

        Args:
            name: Module name
            agent: Agent instance to pass to module

        Returns:
            Module instance or None if failed
        """
        if name not in self.modules:
            logger.error(f"Module not found: {name}")
            return None

        metadata = self.modules[name]

        try:
            # Create instance if not exists
            if metadata.instance is None:
                metadata.instance = metadata.module_class(agent)
                metadata.load_count += 1
                logger.debug(f"Created instance of module: {name}")

            return metadata.instance

        except Exception as e:
            metadata.error_count += 1
            metadata.last_error = str(e)
            logger.error(f"Failed to instantiate module {name}: {e}")
            return None

    def unload_module(self, name: str) -> bool:
        """
        Unload a module instance

        Args:
            name: Module name

        Returns:
            True if unload successful
        """
        if name not in self.modules:
            return False

        try:
            metadata = self.modules[name]

            # Call cleanup if available
            if metadata.instance and hasattr(metadata.instance, 'cleanup'):
                metadata.instance.cleanup()

            metadata.instance = None
            logger.info(f"Unloaded module: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload module {name}: {e}")
            return False

    def reload_module(self, name: str, agent=None) -> Optional[Any]:
        """
        Reload a module (unload and load again)

        Args:
            name: Module name
            agent: Agent instance

        Returns:
            Reloaded module instance
        """
        logger.info(f"Reloading module: {name}")

        # Unload first
        self.unload_module(name)

        # If it's a file-based module, reload the source
        metadata = self.modules.get(name)
        if metadata and metadata.source_path and Path(metadata.source_path).exists():
            try:
                # Remove from registry and reload from file
                del self.modules[name]
                self.load_module_from_file(Path(metadata.source_path))
            except Exception as e:
                logger.error(f"Failed to reload module source {name}: {e}")

        # Load the module
        return self.load_module(name, agent)

    def add_module_path(self, path: Path) -> bool:
        """
        Add a directory to search for modules

        Args:
            path: Directory path

        Returns:
            True if path added successfully
        """
        path = Path(path).expanduser().resolve()

        if not path.exists():
            logger.warning(f"Module path does not exist: {path}")
            return False

        if not path.is_dir():
            logger.warning(f"Module path is not a directory: {path}")
            return False

        if path not in self.module_paths:
            self.module_paths.append(path)
            logger.info(f"Added module path: {path}")

        return True

    def load_all_modules(self, modules_dir: Path) -> Dict[str, Any]:
        """
        Load all modules from a directory

        Args:
            modules_dir: Directory containing modules

        Returns:
            Dictionary of loaded module instances
        """
        modules_dir = Path(modules_dir).expanduser()
        loaded_modules = {}

        if not modules_dir.exists():
            logger.warning(f"Modules directory does not exist: {modules_dir}")
            return loaded_modules

        # Add to module paths
        self.add_module_path(modules_dir)

        # Load Python files as modules
        for file_path in modules_dir.glob("*.py"):
            if file_path.name.startswith('__'):
                continue

            try:
                module_instance = self.load_module_from_file(file_path)
                if module_instance:
                    module_name = file_path.stem
                    loaded_modules[module_name] = module_instance

            except Exception as e:
                logger.error(f"Failed to load module from {file_path}: {e}")

        logger.info(f"Loaded {len(loaded_modules)} modules from {modules_dir}")
        return loaded_modules

    def load_module_from_file(self, file_path: Path) -> Optional[str]:
        """
        Load a module from a Python file

        Args:
            file_path: Path to Python file

        Returns:
            Module name if loaded successfully
        """
        file_path = Path(file_path)

        if not file_path.exists() or not file_path.suffix == '.py':
            logger.error(f"Invalid module file: {file_path}")
            return None

        module_name = file_path.stem

        try:
            # Load module spec
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load module spec: {file_path}")
                return None

            # Create module
            module = importlib.util.module_from_spec(spec)

            # Execute module
            spec.loader.exec_module(module)

            # Find module classes
            module_classes = self._find_module_classes(module)

            if not module_classes:
                logger.warning(f"No module classes found in {file_path}")
                return None

            # Register all found classes
            for class_name, module_class in module_classes.items():
                self.register_module(
                    name=class_name.lower(),
                    module_class=module_class,
                    source_path=str(file_path),
                    description=getattr(module_class, '__doc__', ''),
                    version=getattr(module_class, 'version', '1.0.0')
                )

            return module_name

        except Exception as e:
            logger.error(f"Failed to load module from {file_path}: {e}")
            logger.debug(traceback.format_exc())
            return None

    def _find_module_classes(self, module) -> Dict[str, Type]:
        """
        Find module classes in a loaded module

        Args:
            module: Loaded module object

        Returns:
            Dictionary of class name -> class
        """
        module_classes = {}

        for name in dir(module):
            obj = getattr(module, name)

            # Check if it's a class
            if not isinstance(obj, type):
                continue

            # Skip built-in classes
            if name.startswith('_'):
                continue

            # Check if it looks like a module class
            if (hasattr(obj, '__init__') and
                (name.endswith('Module') or name.endswith('Commands') or
                 hasattr(obj, 'get_commands'))):
                module_classes[name] = obj

        return module_classes

    def get_module_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a module

        Args:
            name: Module name

        Returns:
            Module information dictionary
        """
        if name not in self.modules:
            return None

        metadata = self.modules[name]

        return {
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'source_path': metadata.source_path,
            'loaded_at': metadata.loaded_at,
            'load_count': metadata.load_count,
            'error_count': metadata.error_count,
            'last_error': metadata.last_error,
            'is_loaded': metadata.instance is not None,
            'class_name': metadata.module_class.__name__,
            'actions': self._get_module_actions(metadata)
        }

    def _get_module_actions(self, metadata: ModuleMetadata) -> List[str]:
        """Get list of actions available in a module"""
        if metadata.instance:
            # Get actions from instance
            if hasattr(metadata.instance, 'get_actions'):
                return metadata.instance.get_actions()
            else:
                # Fallback: inspect public methods
                return [
                    name for name in dir(metadata.instance)
                    if not name.startswith('_') and callable(getattr(metadata.instance, name))
                ]
        else:
            # Get actions from class
            return [
                name for name in dir(metadata.module_class)
                if not name.startswith('_') and callable(getattr(metadata.module_class, name))
            ]

    def list_modules(self) -> List[Dict[str, Any]]:
        """
        List all registered modules

        Returns:
            List of module information dictionaries
        """
        return [self.get_module_info(name) for name in self.modules.keys()]

    def search_modules(self, query: str) -> List[Dict[str, Any]]:
        """
        Search modules by name or description

        Args:
            query: Search query

        Returns:
            List of matching modules
        """
        query = query.lower()
        matches = []

        for name, metadata in self.modules.items():
            if (query in name.lower() or
                query in metadata.description.lower() or
                any(query in action.lower() for action in self._get_module_actions(metadata))):
                matches.append(self.get_module_info(name))

        return matches

    def save_registry_state(self, file_path: Path) -> bool:
        """
        Save registry state to file

        Args:
            file_path: File to save state to

        Returns:
            True if save successful
        """
        try:
            state = {
                'modules': {},
                'module_paths': [str(p) for p in self.module_paths],
                'saved_at': datetime.now().isoformat()
            }

            # Save module metadata (excluding instances and classes)
            for name, metadata in self.modules.items():
                state['modules'][name] = {
                    'name': metadata.name,
                    'source_path': metadata.source_path,
                    'description': metadata.description,
                    'version': metadata.version,
                    'loaded_at': metadata.loaded_at,
                    'load_count': metadata.load_count,
                    'error_count': metadata.error_count,
                    'last_error': metadata.last_error
                }

            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Registry state saved to: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save registry state: {e}")
            return False

    def load_registry_state(self, file_path: Path) -> bool:
        """
        Load registry state from file

        Args:
            file_path: File to load state from

        Returns:
            True if load successful
        """
        try:
            if not Path(file_path).exists():
                logger.warning(f"Registry state file not found: {file_path}")
                return False

            with open(file_path, 'r') as f:
                state = json.load(f)

            # Restore module paths
            for path_str in state.get('module_paths', []):
                self.add_module_path(Path(path_str))

            # Reload modules from their source files
            for name, module_data in state.get('modules', {}).items():
                source_path = module_data.get('source_path')
                if source_path and Path(source_path).exists():
                    self.load_module_from_file(Path(source_path))

            logger.info(f"Registry state loaded from: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load registry state: {e}")
            return False

    def cleanup(self):
        """Cleanup registry and unload all modules"""
        logger.info("Cleaning up module registry")

        for name in list(self.modules.keys()):
            self.unload_module(name)

        self.modules.clear()
        self.module_paths.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_modules = len(self.modules)
        loaded_modules = sum(1 for m in self.modules.values() if m.instance is not None)
        total_errors = sum(m.error_count for m in self.modules.values())

        return {
            'total_modules': total_modules,
            'loaded_modules': loaded_modules,
            'unloaded_modules': total_modules - loaded_modules,
            'total_errors': total_errors,
            'module_paths': len(self.module_paths),
            'modules_with_errors': len([m for m in self.modules.values() if m.error_count > 0])
        }

# Global registry instance
_registry = None

def get_registry() -> ModuleRegistry:
    """Get global module registry instance"""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry

if __name__ == "__main__":
    # Test the registry
    registry = ModuleRegistry()

    # Create a test module
    class TestModule:
        def __init__(self, agent):
            self.agent = agent
            self.name = "test"

        def get_commands(self):
            return {"test": self}

        def hello(self):
            return "Hello from test module!"

    # Register and test
    registry.register_module("test", TestModule, "test.py", "Test module")

    # Load module
    module = registry.load_module("test", agent=None)
    print(f"Loaded module: {module}")
    print(f"Module info: {registry.get_module_info('test')}")
    print(f"Registry stats: {registry.get_stats()}")