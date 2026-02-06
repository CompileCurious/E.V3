"""
E.V3 Microkernel
Minimal event loop core with module registry and event bus
"""

from typing import Dict, Any, Optional, Set, List
from loguru import logger
import time
import signal
import sys
from pathlib import Path

from kernel.module import Module, ModuleState, Permission, KernelAPI


class EventBus:
    """
    Central event bus for module communication
    Thread-safe event dispatch with subscription management
    """
    
    def __init__(self):
        self._subscriptions: Dict[str, Set[str]] = {}  # event_type -> set of module names
        self._handlers: Dict[str, Module] = {}  # module_name -> Module instance
    
    def register_module(self, module: Module):
        """Register a module's event handler"""
        self._handlers[module.get_name()] = module
        logger.debug(f"Registered event handler for module '{module.get_name()}'")
    
    def unregister_module(self, module_name: str):
        """Unregister a module"""
        if module_name in self._handlers:
            del self._handlers[module_name]
        
        # Remove from all subscriptions
        for subscribers in self._subscriptions.values():
            subscribers.discard(module_name)
        
        logger.debug(f"Unregistered module '{module_name}' from event bus")
    
    def subscribe(self, event_type: str, module_name: str) -> bool:
        """Subscribe a module to an event type"""
        if module_name not in self._handlers:
            logger.error(f"Cannot subscribe unregistered module '{module_name}'")
            return False
        
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = set()
        
        self._subscriptions[event_type].add(module_name)
        logger.debug(f"Module '{module_name}' subscribed to '{event_type}'")
        return True
    
    def unsubscribe(self, event_type: str, module_name: str):
        """Unsubscribe a module from an event type"""
        if event_type in self._subscriptions:
            self._subscriptions[event_type].discard(module_name)
    
    def emit(self, event_type: str, event_data: Dict[str, Any], source: str) -> bool:
        """Emit an event to all subscribers"""
        if event_type not in self._subscriptions:
            logger.debug(f"No subscribers for event '{event_type}'")
            return True
        
        subscribers = self._subscriptions[event_type].copy()
        logger.debug(f"Emitting '{event_type}' from '{source}' to {len(subscribers)} subscribers")
        
        for module_name in subscribers:
            if module_name == source:
                continue  # Don't send event back to source
            
            module = self._handlers.get(module_name)
            if not module:
                continue
            
            try:
                module.handle_event(event_type, event_data)
            except Exception as e:
                logger.error(f"Error handling event '{event_type}' in module '{module_name}': {e}")
        
        return True


class PermissionChecker:
    """
    Permission checker with scoped storage model
    Each module has isolated storage and must declare required permissions
    """
    
    def __init__(self):
        self._grants: Dict[str, Set[Permission]] = {}  # module_name -> set of granted permissions
    
    def grant(self, module_name: str, permissions: Set[Permission]):
        """Grant permissions to a module"""
        if module_name not in self._grants:
            self._grants[module_name] = set()
        
        self._grants[module_name].update(permissions)
        logger.debug(f"Granted {len(permissions)} permissions to '{module_name}'")
    
    def revoke(self, module_name: str):
        """Revoke all permissions from a module"""
        if module_name in self._grants:
            del self._grants[module_name]
            logger.debug(f"Revoked permissions from '{module_name}'")
    
    def check(self, module_name: str, permission: Permission) -> bool:
        """Check if module has a specific permission"""
        return permission in self._grants.get(module_name, set())
    
    def get_permissions(self, module_name: str) -> Set[Permission]:
        """Get all permissions for a module"""
        return self._grants.get(module_name, set()).copy()


class ConfigStore:
    """
    Scoped configuration storage
    Each module has isolated configuration namespace
    """
    
    def __init__(self, global_config: Dict[str, Any]):
        self._global_config = global_config
        self._module_storage: Dict[str, Dict[str, Any]] = {}
    
    def get(self, module_name: str, key: str) -> Optional[Any]:
        """Get configuration value for module"""
        # Check module-specific storage first
        if module_name in self._module_storage:
            if key in self._module_storage[module_name]:
                return self._module_storage[module_name][key]
        
        # Fall back to global config
        return self._global_config.get(module_name, {}).get(key)
    
    def set(self, module_name: str, key: str, value: Any) -> bool:
        """Set configuration value for module"""
        if module_name not in self._module_storage:
            self._module_storage[module_name] = {}
        
        self._module_storage[module_name][key] = value
        return True
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get entire configuration for module"""
        return self._global_config.get(module_name, {})


class ModuleRegistry:
    """
    Module registry with dependency resolution
    Manages module lifecycle: load -> enable -> disable -> shutdown
    """
    
    def __init__(self, kernel_api: KernelAPI, permission_checker: PermissionChecker, event_bus: EventBus):
        self._modules: Dict[str, Module] = {}
        self._kernel_api = kernel_api
        self._permission_checker = permission_checker
        self._event_bus = event_bus
    
    def register(self, module: Module) -> bool:
        """Register a module"""
        name = module.get_name()
        
        if name in self._modules:
            logger.error(f"Module '{name}' already registered")
            return False
        
        # Grant requested permissions
        permissions = module.get_required_permissions()
        self._permission_checker.grant(name, permissions)
        
        # Register with event bus
        self._event_bus.register_module(module)
        
        # Add to registry
        self._modules[name] = module
        logger.info(f"Module '{name}' registered with {len(permissions)} permissions")
        
        return True
    
    def unregister(self, module_name: str) -> bool:
        """Unregister a module"""
        if module_name not in self._modules:
            return False
        
        module = self._modules[module_name]
        
        # Ensure module is shutdown
        if module.get_state() not in [ModuleState.UNLOADED, ModuleState.LOADED]:
            self.shutdown_module(module_name)
        
        # Revoke permissions
        self._permission_checker.revoke(module_name)
        
        # Unregister from event bus
        self._event_bus.unregister_module(module_name)
        
        # Remove from registry
        del self._modules[module_name]
        logger.info(f"Module '{module_name}' unregistered")
        
        return True
    
    def load_module(self, module_name: str, config: Dict[str, Any]) -> bool:
        """Load a module"""
        module = self._modules.get(module_name)
        if not module:
            logger.error(f"Module '{module_name}' not found")
            return False
        
        # Check dependencies
        deps = module.get_dependencies()
        for dep in deps:
            if dep not in self._modules:
                logger.error(f"Module '{module_name}' depends on unregistered module '{dep}'")
                return False
            
            dep_state = self._modules[dep].get_state()
            if dep_state not in [ModuleState.LOADED, ModuleState.ENABLED]:
                logger.error(f"Dependency '{dep}' of '{module_name}' not loaded")
                return False
        
        # Load module
        try:
            if module.load(config):
                module.state = ModuleState.LOADED
                logger.info(f"Module '{module_name}' loaded")
                return True
            else:
                logger.error(f"Module '{module_name}' load failed")
                module.state = ModuleState.ERROR
                return False
        except Exception as e:
            logger.error(f"Exception loading module '{module_name}': {e}")
            module.state = ModuleState.ERROR
            return False
    
    def enable_module(self, module_name: str) -> bool:
        """Enable a module"""
        module = self._modules.get(module_name)
        if not module:
            return False
        
        if module.get_state() != ModuleState.LOADED:
            logger.error(f"Module '{module_name}' must be loaded before enabling")
            return False
        
        try:
            if module.enable():
                module.state = ModuleState.ENABLED
                logger.info(f"Module '{module_name}' enabled")
                return True
            else:
                logger.error(f"Module '{module_name}' enable failed")
                return False
        except Exception as e:
            logger.error(f"Exception enabling module '{module_name}': {e}")
            module.state = ModuleState.ERROR
            return False
    
    def disable_module(self, module_name: str) -> bool:
        """Disable a module"""
        module = self._modules.get(module_name)
        if not module:
            return False
        
        if module.get_state() != ModuleState.ENABLED:
            return True
        
        try:
            if module.disable():
                module.state = ModuleState.DISABLED
                logger.info(f"Module '{module_name}' disabled")
                return True
            else:
                logger.error(f"Module '{module_name}' disable failed")
                return False
        except Exception as e:
            logger.error(f"Exception disabling module '{module_name}': {e}")
            return False
    
    def shutdown_module(self, module_name: str) -> bool:
        """Shutdown a module"""
        module = self._modules.get(module_name)
        if not module:
            return False
        
        try:
            # Disable first if enabled
            if module.get_state() == ModuleState.ENABLED:
                self.disable_module(module_name)
            
            if module.shutdown():
                module.state = ModuleState.UNLOADED
                logger.info(f"Module '{module_name}' shutdown")
                return True
            else:
                logger.error(f"Module '{module_name}' shutdown failed")
                return False
        except Exception as e:
            logger.error(f"Exception shutting down module '{module_name}': {e}")
            return False
    
    def get_module(self, module_name: str) -> Optional[Module]:
        """Get a module by name"""
        return self._modules.get(module_name)
    
    def get_all_modules(self) -> Dict[str, Module]:
        """Get all registered modules"""
        return self._modules.copy()
    
    def get_enabled_modules(self) -> List[str]:
        """Get names of all enabled modules"""
        return [name for name, mod in self._modules.items() if mod.get_state() == ModuleState.ENABLED]


class Kernel:
    """
    E.V3 Microkernel
    Minimal core with event loop, module management, and permission boundaries
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        # Initialize core components
        self._permission_checker = PermissionChecker()
        self._event_bus = EventBus()
        self._config_store = ConfigStore(config)
        
        # Create kernel API
        self._kernel_api = KernelAPI(
            self._permission_checker,
            self._event_bus,
            self._config_store
        )
        
        # Initialize module registry
        self._module_registry = ModuleRegistry(
            self._kernel_api,
            self._permission_checker,
            self._event_bus
        )
        
        logger.info("Microkernel initialized")
    
    def register_module(self, module: Module) -> bool:
        """Register a capability module"""
        return self._module_registry.register(module)
    
    def load_modules(self, module_configs: Dict[str, Dict[str, Any]]) -> bool:
        """Load all registered modules with their configurations"""
        success = True
        
        for module_name, config in module_configs.items():
            if not self._module_registry.load_module(module_name, config):
                logger.error(f"Failed to load module '{module_name}'")
                success = False
        
        return success
    
    def enable_modules(self) -> bool:
        """Enable all loaded modules"""
        success = True
        
        for module_name in self._module_registry.get_all_modules():
            module = self._module_registry.get_module(module_name)
            if module and module.get_state() == ModuleState.LOADED:
                if not self._module_registry.enable_module(module_name):
                    logger.error(f"Failed to enable module '{module_name}'")
                    success = False
        
        return success
    
    def start(self):
        """Start the kernel event loop"""
        if self.running:
            logger.warning("Kernel already running")
            return
        
        logger.info("Starting microkernel event loop...")
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Main event loop
        try:
            while self.running:
                time.sleep(0.1)  # Minimal sleep, events are async via modules
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the kernel and shutdown all modules"""
        if not self.running:
            return
        
        logger.info("Stopping microkernel...")
        self.running = False
        
        # Shutdown modules in reverse order
        modules = list(self._module_registry.get_all_modules().keys())
        for module_name in reversed(modules):
            self._module_registry.shutdown_module(module_name)
        
        logger.info("Microkernel stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Signal {signum} received, shutting down...")
        self.stop()
        sys.exit(0)
    
    def get_kernel_api(self) -> KernelAPI:
        """Get kernel API for module creation"""
        return self._kernel_api
