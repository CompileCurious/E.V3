"""
Microkernel Module Interface
Defines the contract for all capability modules in the E.V3 kernel
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
from enum import Enum
from loguru import logger


class ModuleState(Enum):
    """Module lifecycle states"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class Permission(Enum):
    """System permissions that modules can request"""
    # IPC permissions
    IPC_SEND = "ipc.send"
    IPC_RECEIVE = "ipc.receive"
    
    # Event permissions
    EVENT_EMIT = "event.emit"
    EVENT_SUBSCRIBE = "event.subscribe"
    
    # Storage permissions
    STORAGE_READ = "storage.read"
    STORAGE_WRITE = "storage.write"
    
    # System monitoring permissions
    SYSTEM_EVENTS = "system.events"
    SECURITY_EVENTS = "security.events"
    CALENDAR_READ = "calendar.read"
    
    # LLM permissions
    LLM_LOCAL = "llm.local"
    LLM_EXTERNAL = "llm.external"


class Module(ABC):
    """
    Base class for all microkernel modules
    Each module is an isolated capability with explicit lifecycle and permissions
    """
    
    def __init__(self, name: str, kernel_api: 'KernelAPI'):
        self.name = name
        self.kernel = kernel_api
        self.state = ModuleState.UNLOADED
        self.config: Dict[str, Any] = {}
        
        logger.debug(f"Module '{name}' initialized")
    
    @abstractmethod
    def get_required_permissions(self) -> Set[Permission]:
        """
        Declare permissions required by this module
        Returns: Set of Permission enums
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> Set[str]:
        """
        Declare module dependencies (other module names)
        Returns: Set of module name strings
        """
        pass
    
    @abstractmethod
    def load(self, config: Dict[str, Any]) -> bool:
        """
        Load module with configuration
        Initialize resources, validate config, prepare for enable
        Returns: True if loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def enable(self) -> bool:
        """
        Enable module - start active operations
        Begin processing events, start background threads, etc.
        Returns: True if enabled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def disable(self) -> bool:
        """
        Disable module - stop active operations
        Stop processing, pause background threads, but keep resources
        Returns: True if disabled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Shutdown module - release all resources
        Clean up threads, close files, disconnect services
        Returns: True if shutdown successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle an event from the event bus
        Args:
            event_type: Type/topic of the event
            event_data: Event payload
        """
        pass
    
    def get_state(self) -> ModuleState:
        """Get current module state"""
        return self.state
    
    def get_name(self) -> str:
        """Get module name"""
        return self.name


class KernelAPI:
    """
    API interface provided by kernel to modules
    Enforces permission boundaries and provides core services
    """
    
    def __init__(self, permission_checker, event_bus, config_store):
        self._permission_checker = permission_checker
        self._event_bus = event_bus
        self._config_store = config_store
    
    def emit_event(self, module_name: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Emit an event to the event bus
        Requires: Permission.EVENT_EMIT
        """
        if not self._permission_checker.check(module_name, Permission.EVENT_EMIT):
            logger.warning(f"Module '{module_name}' denied EVENT_EMIT permission")
            return False
        
        return self._event_bus.emit(event_type, event_data, source=module_name)
    
    def subscribe_event(self, module_name: str, event_type: str) -> bool:
        """
        Subscribe to an event type
        Requires: Permission.EVENT_SUBSCRIBE
        """
        if not self._permission_checker.check(module_name, Permission.EVENT_SUBSCRIBE):
            logger.warning(f"Module '{module_name}' denied EVENT_SUBSCRIBE permission")
            return False
        
        return self._event_bus.subscribe(event_type, module_name)
    
    def read_config(self, module_name: str, key: str) -> Optional[Any]:
        """
        Read configuration value
        Requires: Permission.STORAGE_READ
        """
        if not self._permission_checker.check(module_name, Permission.STORAGE_READ):
            logger.warning(f"Module '{module_name}' denied STORAGE_READ permission")
            return None
        
        return self._config_store.get(module_name, key)
    
    def write_config(self, module_name: str, key: str, value: Any) -> bool:
        """
        Write configuration value
        Requires: Permission.STORAGE_WRITE
        """
        if not self._permission_checker.check(module_name, Permission.STORAGE_WRITE):
            logger.warning(f"Module '{module_name}' denied STORAGE_WRITE permission")
            return False
        
        return self._config_store.set(module_name, key, value)
    
    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """Get state of another module (no permission required)"""
        # This is implemented by the kernel's module registry
        return None
