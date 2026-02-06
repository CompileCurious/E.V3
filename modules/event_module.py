"""
Event Monitoring Module
Monitors Windows system events (Defender, Firewall, System notifications)
"""

from typing import Dict, Any, Set
from loguru import logger

from kernel.module import Module, Permission, KernelAPI
from service.events.event_listeners import DefenderEventListener, FirewallEventListener, WindowsEventListener


class EventModule(Module):
    """
    System event monitoring capability module
    Monitors Windows events and emits to event bus
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("events", kernel_api)
        self.listeners: Dict[str, WindowsEventListener] = {}
    
    def get_required_permissions(self) -> Set[Permission]:
        """Event module needs system monitoring and event emission"""
        return {
            Permission.SYSTEM_EVENTS,
            Permission.SECURITY_EVENTS,
            Permission.EVENT_EMIT,
            Permission.STORAGE_READ,
        }
    
    def get_dependencies(self) -> Set[str]:
        """Depends on state module to trigger alerts"""
        return {"state"}
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize event listeners"""
        try:
            self.config = config
            events_config = config.get("events", {})
            
            # Setup Windows Defender listener
            if events_config.get("windows_defender", {}).get("enabled", True):
                event_ids = events_config.get("windows_defender", {}).get("event_ids")
                defender_listener = DefenderEventListener(event_ids)
                defender_listener.register_callback(self._on_defender_event)
                self.listeners["defender"] = defender_listener
                logger.debug("Defender listener configured")
            
            # Setup Firewall listener
            if events_config.get("firewall", {}).get("enabled", True):
                firewall_listener = FirewallEventListener()
                firewall_listener.register_callback(self._on_firewall_event)
                self.listeners["firewall"] = firewall_listener
                logger.debug("Firewall listener configured")
            
            logger.info("Event module loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load event module: {e}")
            return False
    
    def enable(self) -> bool:
        """Start monitoring events"""
        try:
            for name, listener in self.listeners.items():
                listener.start()
                logger.debug(f"Started {name} listener")
            
            logger.info(f"Event module enabled with {len(self.listeners)} listeners")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable event module: {e}")
            return False
    
    def disable(self) -> bool:
        """Stop monitoring events"""
        try:
            for name, listener in self.listeners.items():
                listener.stop()
                logger.debug(f"Stopped {name} listener")
            
            logger.info("Event module disabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable event module: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Cleanup listeners"""
        self.disable()
        self.listeners.clear()
        logger.info("Event module shutdown")
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Not subscribed to any events currently"""
        pass
    
    def _on_defender_event(self, event_data: Dict[str, Any]):
        """Handle Windows Defender event"""
        logger.info(f"Defender event detected: ID {event_data.get('event_id')}")
        
        # Emit to event bus for LLM interpretation
        self.kernel.emit_event(self.name, "system.defender", event_data)
    
    def _on_firewall_event(self, event_data: Dict[str, Any]):
        """Handle firewall event"""
        logger.info(f"Firewall event detected: ID {event_data.get('event_id')}")
        
        # Emit to event bus for LLM interpretation
        self.kernel.emit_event(self.name, "system.firewall", event_data)


class FirewallEventListener(WindowsEventListener):
    """Windows Firewall event listener"""
    
    def __init__(self):
        super().__init__(
            "Security",
            [4946, 4947, 4948, 4950, 4954, 4956]  # Firewall rule change events
        )
    
    def _anonymize_event(self, event) -> Dict[str, Any]:
        """Anonymize firewall event"""
        base_data = super()._anonymize_event(event)
        base_data.update({
            "rule_change": True,
            "firewall_event": True,
        })
        return base_data
