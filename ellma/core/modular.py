"""
ELLMa Modular System Core

This module provides the core modular system functionality including
module interfaces, dependency injection, and inter-module communication.
"""

import abc
import inspect
import asyncio
from typing import Dict, List, Any, Optional, Type, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import threading
import weakref

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class ModuleState(Enum):
    """Module lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    UNLOADING = "unloading"

class ModulePriority(Enum):
    """Module execution priorities"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class ModuleMetrics:
    """Module performance metrics"""
    calls_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None

@dataclass
class ModuleCapability:
    """Represents a module capability"""
    name: str
    description: str
    input_types: List[Type] = field(default_factory=list)
    output_type: Optional[Type] = None
    async_capable: bool = False
    dependencies: List[str] = field(default_factory=list)

class IModule(abc.ABC):
    """
    Interface for ELLMa modules

    All modules must implement this interface to be properly
    integrated into the ELLMa system.
    """

    @abc.abstractmethod
    def get_name(self) -> str:
        """Get module name"""
        pass

    @abc.abstractmethod
    def get_version(self) -> str:
        """Get module version"""
        pass

    @abc.abstractmethod
    def get_capabilities(self) -> List[ModuleCapability]:
        """Get module capabilities"""
        pass

    @abc.abstractmethod
    def initialize(self, context: 'ModuleContext') -> bool:
        """Initialize the module"""
        pass

    @abc.abstractmethod
    def shutdown(self) -> bool:
        """Shutdown the module"""
        pass

    def get_dependencies(self) -> List[str]:
        """Get module dependencies"""
        return []

    def get_priority(self) -> ModulePriority:
        """Get module priority"""
        return ModulePriority.NORMAL

    def supports_async(self) -> bool:
        """Check if module supports async operations"""
        return False

class ModuleContext:
    """
    Context provided to modules for system interaction

    Provides access to other modules, system services,
    and inter-module communication.
    """

    def __init__(self, module_manager: 'ModuleManager'):
        self.module_manager = module_manager
        self._module_refs: Dict[str, weakref.ref] = {}
        self._event_bus = EventBus()
        self._shared_data: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def get_module(self, module_name: str) -> Optional[IModule]:
        """Get reference to another module"""
        return self.module_manager.get_module(module_name)

    def call_module(self, module_name: str, method_name: str, *args, **kwargs) -> Any:
        """Call method on another module"""
        module = self.get_module(module_name)
        if module is None:
            raise RuntimeError(f"Module {module_name} not found")

        if not hasattr(module, method_name):
            raise RuntimeError(f"Method {method_name} not found in module {module_name}")

        method = getattr(module, method_name)
        return method(*args, **kwargs)

    def emit_event(self, event_name: str, data: Any = None):
        """Emit an event to other modules"""
        self._event_bus.emit(event_name, data)

    def subscribe_event(self, event_name: str, callback: Callable):
        """Subscribe to events from other modules"""
        self._event_bus.subscribe(event_name, callback)

    def set_shared_data(self, key: str, value: Any):
        """Set shared data accessible by all modules"""
        with self._lock:
            self._shared_data[key] = value

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data"""
        with self._lock:
            return self._shared_data.get(key, default)

class EventBus:
    """Simple event bus for inter-module communication"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, callback: Callable):
        """Subscribe to an event"""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable):
        """Unsubscribe from an event"""
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                except ValueError:
                    pass

    def emit(self, event_name: str, data: Any = None):
        """Emit an event to all subscribers"""
        with self._lock:
            callbacks = self._subscribers.get(event_name, []).copy()

        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_name}: {e}")

class ModuleManager:
    """
    Core module manager for ELLMa

    Manages the lifecycle of modules, handles dependencies,
    and provides inter-module communication.
    """

    def __init__(self, agent=None):
        self.agent = agent
        self._modules: Dict[str, IModule] = {}
        self._module_states: Dict[str, ModuleState] = {}
        self._module_metrics: Dict[str, ModuleMetrics] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        self._context = ModuleContext(self)
        self._lock = threading.RLock()

        # Module execution settings
        self.max_init_time = 30.0  # seconds
        self.shutdown_timeout = 10.0  # seconds

    def register_module(self, module: IModule) -> bool:
        """
        Register a module with the system

        Args:
            module: Module instance to register

        Returns:
            True if registration successful
        """
        module_name = module.get_name()

        with self._lock:
            if module_name in self._modules:
                logger.warning(f"Module {module_name} already registered")
                return False

            try:
                # Validate module
                if not self._validate_module(module):
                    return False

                # Store module
                self._modules[module_name] = module
                self._module_states[module_name] = ModuleState.UNLOADED
                self._module_metrics[module_name] = ModuleMetrics()

                # Build dependency graph
                dependencies = module.get_dependencies()
                self._dependency_graph[module_name] = dependencies

                logger.info(f"Registered module: {module_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to register module {module_name}: {e}")
                return False

    def unregister_module(self, module_name: str) -> bool:
        """
        Unregister a module

        Args:
            module_name: Name of module to unregister

        Returns:
            True if successful
        """
        with self._lock:
            if module_name not in self._modules:
                return False

            try:
                # Shutdown module if active
                if self._module_states[module_name] in [ModuleState.LOADED, ModuleState.ACTIVE]:
                    self.shutdown_module(module_name)

                # Remove from tracking
                del self._modules[module_name]
                del self._module_states[module_name]
                del self._module_metrics[module_name]
                del self._dependency_graph[module_name]

                logger.info(f"Unregistered module: {module_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to unregister module {module_name}: {e}")
                return False

    def initialize_module(self, module_name: str) -> bool:
        """
        Initialize a module

        Args:
            module_name: Name of module to initialize

        Returns:
            True if successful
        """
        with self._lock:
            if module_name not in self._modules:
                logger.error(f"Module {module_name} not found")
                return False

            module = self._modules[module_name]

            # Check if already initialized
            current_state = self._module_states[module_name]
            if current_state in [ModuleState.LOADED, ModuleState.ACTIVE]:
                return True

            try:
                # Set loading state
                self._module_states[module_name] = ModuleState.LOADING

                # Initialize dependencies first
                dependencies = self._dependency_graph.get(module_name, [])
                for dep_name in dependencies:
                    if not self.initialize_module(dep_name):
                        self._module_states[module_name] = ModuleState.ERROR
                        return False

                # Initialize the module
                start_time = time.time()
                success = module.initialize(self._context)
                init_time = time.time() - start_time

                if init_time > self.max_init_time:
                    logger.warning(f"Module {module_name} took {init_time:.2f}s to initialize")

                if success:
                    self._module_states[module_name] = ModuleState.LOADED
                    logger.info(f"Initialized module: {module_name}")

                    # Emit initialization event
                    self._context.emit_event('module_initialized', {
                        'module_name': module_name,
                        'init_time': init_time
                    })

                    return True
                else:
                    self._module_states[module_name] = ModuleState.ERROR
                    logger.error(f"Module {module_name} initialization failed")
                    return False

            except Exception as e:
                self._module_states[module_name] = ModuleState.ERROR
                logger.error(f"Error initializing module {module_name}: {e}")
                return False

    def shutdown_module(self, module_name: str) -> bool:
        """
        Shutdown a module

        Args:
            module_name: Name of module to shutdown

        Returns:
            True if successful
        """
        with self._lock:
            if module_name not in self._modules:
                return False

            module = self._modules[module_name]
            current_state = self._module_states[module_name]

            if current_state == ModuleState.UNLOADED:
                return True

            try:
                self._module_states[module_name] = ModuleState.UNLOADING

                # Shutdown with timeout
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Module {module_name} shutdown timed out")

                try:
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(self.shutdown_timeout))

                    success = module.shutdown()

                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

                except AttributeError:
                    # Windows doesn't support SIGALRM
                    success = module.shutdown()
                except TimeoutError:
                    logger.error(f"Module {module_name} shutdown timed out")
                    success = False

                if success:
                    self._module_states[module_name] = ModuleState.UNLOADED
                    logger.info(f"Shutdown module: {module_name}")

                    # Emit shutdown event
                    self._context.emit_event('module_shutdown', {
                        'module_name': module_name
                    })

                    return True
                else:
                    self._module_states[module_name] = ModuleState.ERROR
                    return False

            except Exception as e:
                self._module_states[module_name] = ModuleState.ERROR
                logger.error(f"Error shutting down module {module_name}: {e}")
                return False

    def get_module(self, module_name: str) -> Optional[IModule]:
        """Get module by name"""
        return self._modules.get(module_name)

    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """Get module state"""
        return self._module_states.get(module_name)

    def get_module_metrics(self, module_name: str) -> Optional[ModuleMetrics]:
        """Get module metrics"""
        return self._module_metrics.get(module_name)

    def list_modules(self) -> List[str]:
        """Get list of registered modules"""
        return list(self._modules.keys())

    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive module information"""
        if module_name not in self._modules:
            return None

        module = self._modules[module_name]
        state = self._module_states[module_name]
        metrics = self._module_metrics[module_name]

        return {
            'name': module.get_name(),
            'version': module.get_version(),
            'state': state.value,
            'priority': module.get_priority().value,
            'dependencies': self._dependency_graph.get(module_name, []),
            'capabilities': [cap.__dict__ for cap in module.get_capabilities()],
            'supports_async': module.supports_async(),
            'metrics': {
                'calls_count': metrics.calls_count,
                'total_execution_time': metrics.total_execution_time,
                'average_execution_time': metrics.average_execution_time,
                'error_count': metrics.error_count,
                'last_error': metrics.last_error
            }
        }

    def initialize_all_modules(self) -> Dict[str, bool]:
        """Initialize all registered modules in dependency order"""
        results = {}

        # Get dependency order
        initialization_order = self._get_initialization_order()

        for module_name in initialization_order:
            results[module_name] = self.initialize_module(module_name)

        return results

    def shutdown_all_modules(self) -> Dict[str, bool]:
        """Shutdown all modules in reverse dependency order"""
        results = {}

        # Get reverse dependency order
        shutdown_order = list(reversed(self._get_initialization_order()))

        for module_name in shutdown_order:
            results[module_name] = self.shutdown_module(module_name)

        return results

    def call_module_method(self, module_name: str, method_name: str,
                          *args, **kwargs) -> Any:
        """
        Call a method on a module with metrics tracking

        Args:
            module_name: Target module name
            method_name: Method to call
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Method result
        """
        import time

        if module_name not in self._modules:
            raise RuntimeError(f"Module {module_name} not found")

        module = self._modules[module_name]
        metrics = self._module_metrics[module_name]

        if not hasattr(module, method_name):
            raise RuntimeError(f"Method {method_name} not found in module {module_name}")

        method = getattr(module, method_name)

        # Track metrics
        start_time = time.time()
        metrics.calls_count += 1

        try:
            result = method(*args, **kwargs)

            # Update metrics
            execution_time = time.time() - start_time
            metrics.total_execution_time += execution_time
            metrics.average_execution_time = (
                metrics.total_execution_time / metrics.calls_count
            )

            return result

        except Exception as e:
            # Update error metrics
            metrics.error_count += 1
            metrics.last_error = str(e)

            execution_time = time.time() - start_time
            metrics.total_execution_time += execution_time
            metrics.average_execution_time = (
                metrics.total_execution_time / metrics.calls_count
            )

            raise

    def find_modules_by_capability(self, capability_name: str) -> List[str]:
        """Find modules that provide a specific capability"""
        matching_modules = []

        for module_name, module in self._modules.items():
            capabilities = module.get_capabilities()
            for cap in capabilities:
                if cap.name == capability_name:
                    matching_modules.append(module_name)
                    break

        return matching_modules

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health information"""
        total_modules = len(self._modules)
        loaded_modules = sum(1 for state in self._module_states.values()
                           if state in [ModuleState.LOADED, ModuleState.ACTIVE])
        error_modules = sum(1 for state in self._module_states.values()
                          if state == ModuleState.ERROR)

        total_calls = sum(m.calls_count for m in self._module_metrics.values())
        total_errors = sum(m.error_count for m in self._module_metrics.values())

        return {
            'total_modules': total_modules,
            'loaded_modules': loaded_modules,
            'error_modules': error_modules,
            'health_score': (loaded_modules / total_modules * 100) if total_modules > 0 else 0,
            'total_calls': total_calls,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_calls * 100) if total_calls > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }

    def _validate_module(self, module: IModule) -> bool:
        """Validate module interface compliance"""
        try:
            # Check required methods
            required_methods = ['get_name', 'get_version', 'get_capabilities',
                              'initialize', 'shutdown']

            for method_name in required_methods:
                if not hasattr(module, method_name):
                    logger.error(f"Module missing required method: {method_name}")
                    return False

                method = getattr(module, method_name)
                if not callable(method):
                    logger.error(f"Module method {method_name} is not callable")
                    return False

            # Validate method signatures
            sig = inspect.signature(module.initialize)
            if len(sig.parameters) != 1:
                logger.error("Module initialize method must accept exactly one parameter (context)")
                return False

            # Test basic method calls
            name = module.get_name()
            if not isinstance(name, str) or not name:
                logger.error("Module get_name must return non-empty string")
                return False

            version = module.get_version()
            if not isinstance(version, str) or not version:
                logger.error("Module get_version must return non-empty string")
                return False

            capabilities = module.get_capabilities()
            if not isinstance(capabilities, list):
                logger.error("Module get_capabilities must return list")
                return False

            return True

        except Exception as e:
            logger.error(f"Module validation failed: {e}")
            return False

    def _get_initialization_order(self) -> List[str]:
        """Get module initialization order based on dependencies"""
        # Topological sort of dependency graph
        visited = set()
        temp_visited = set()
        order = []

        def visit(module_name: str):
            if module_name in temp_visited:
                raise RuntimeError(f"Circular dependency detected involving {module_name}")

            if module_name in visited:
                return

            temp_visited.add(module_name)

            # Visit dependencies first
            dependencies = self._dependency_graph.get(module_name, [])
            for dep in dependencies:
                if dep in self._modules:  # Only visit registered modules
                    visit(dep)

            temp_visited.remove(module_name)
            visited.add(module_name)
            order.append(module_name)

        # Visit all modules
        for module_name in self._modules:
            if module_name not in visited:
                visit(module_name)

        return order

class BaseModule(IModule):
    """
    Base implementation of IModule interface

    Provides common functionality for ELLMa modules.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.context: Optional[ModuleContext] = None
        self._capabilities: List[ModuleCapability] = []
        self._initialized = False

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def get_capabilities(self) -> List[ModuleCapability]:
        return self._capabilities.copy()

    def add_capability(self, capability: ModuleCapability):
        """Add a capability to this module"""
        self._capabilities.append(capability)

    def initialize(self, context: ModuleContext) -> bool:
        """Base initialization"""
        try:
            self.context = context

            # Call custom initialization
            success = self._initialize()

            if success:
                self._initialized = True
                logger.info(f"Module {self.name} initialized successfully")

            return success

        except Exception as e:
            logger.error(f"Module {self.name} initialization failed: {e}")
            return False

    def shutdown(self) -> bool:
        """Base shutdown"""
        try:
            if self._initialized:
                success = self._shutdown()
                if success:
                    self._initialized = False
                    self.context = None
                return success
            return True

        except Exception as e:
            logger.error(f"Module {self.name} shutdown failed: {e}")
            return False

    def _initialize(self) -> bool:
        """Override this method for custom initialization"""
        return True

    def _shutdown(self) -> bool:
        """Override this method for custom shutdown"""
        return True

    def is_initialized(self) -> bool:
        """Check if module is initialized"""
        return self._initialized

    def emit_event(self, event_name: str, data: Any = None):
        """Emit an event through the context"""
        if self.context:
            self.context.emit_event(event_name, data)

    def subscribe_event(self, event_name: str, callback: Callable):
        """Subscribe to an event through the context"""
        if self.context:
            self.context.subscribe_event(event_name, callback)

# Global module manager instance
_module_manager = None

def get_module_manager(agent=None) -> ModuleManager:
    """Get global module manager instance"""
    global _module_manager
    if _module_manager is None:
        _module_manager = ModuleManager(agent)
    return _module_manager

if __name__ == "__main__":
    # Test the modular system
    import time

    class TestModule(BaseModule):
        def __init__(self):
            super().__init__("test_module", "1.0.0")
            self.add_capability(ModuleCapability(
                name="test_capability",
                description="Test capability"
            ))

        def _initialize(self) -> bool:
            print(f"Initializing {self.name}")
            return True

        def _shutdown(self) -> bool:
            print(f"Shutting down {self.name}")
            return True

        def test_method(self) -> str:
            return f"Hello from {self.name}"

    # Test module manager
    manager = ModuleManager()

    # Register module
    test_module = TestModule()
    success = manager.register_module(test_module)
    print(f"Module registration: {success}")

    # Initialize module
    success = manager.initialize_module("test_module")
    print(f"Module initialization: {success}")

    # Call module method
    try:
        result = manager.call_module_method("test_module", "test_method")
        print(f"Method call result: {result}")
    except Exception as e:
        print(f"Method call failed: {e}")

    # Get module info
    info = manager.get_module_info("test_module")
    print(f"Module info: {info}")

    # Get system health
    health = manager.get_system_health()
    print(f"System health: {health}")

    # Shutdown module
    success = manager.shutdown_module("test_module")
    print(f"Module shutdown: {success}")

    print("Modular system test completed")