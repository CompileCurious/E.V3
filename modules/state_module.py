"""
State Machine Module
Manages companion states: idle, scanning, alert, reminder
"""

from typing import Dict, Any, Set, Optional, Callable
from loguru import logger
from transitions import Machine

from kernel.module import Module, Permission, KernelAPI
from service.state.state_machine import CompanionState, StateData


class StateModule(Module):
    """
    State machine capability module
    Manages state transitions and notifies other modules via events
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("state", kernel_api)
        self.machine: Optional[Machine] = None
        self.current_state_data: Optional[StateData] = None
        self._state_callbacks: Dict[str, list] = {}
    
    def get_required_permissions(self) -> Set[Permission]:
        """State module emits events and subscribes to transition requests"""
        return {
            Permission.EVENT_EMIT,
            Permission.EVENT_SUBSCRIBE,
            Permission.STORAGE_READ,
            Permission.STORAGE_WRITE,
        }
    
    def get_dependencies(self) -> Set[str]:
        """No dependencies - state is fundamental"""
        return set()
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize state machine"""
        try:
            self.config = config
            
            # Setup state callbacks storage
            states = [
                CompanionState.IDLE.value,
                CompanionState.SCANNING.value,
                CompanionState.ALERT.value,
                CompanionState.REMINDER.value,
            ]
            self._state_callbacks = {state: [] for state in states}
            
            # Initialize transitions state machine
            self.machine = Machine(
                model=self,
                states=states,
                initial=CompanionState.IDLE.value,
                auto_transitions=False
            )
            
            self._setup_transitions()
            
            logger.info("State module loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load state module: {e}")
            return False
    
    def enable(self) -> bool:
        """Start state machine operations"""
        try:
            # Subscribe to state transition requests from other modules
            self.kernel.subscribe_event(self.name, "state.transition.alert")
            self.kernel.subscribe_event(self.name, "state.transition.reminder")
            self.kernel.subscribe_event(self.name, "state.transition.scanning")
            self.kernel.subscribe_event(self.name, "state.transition.idle")
            
            # Emit initial state
            self._emit_state_change(CompanionState.IDLE, StateData("Ready", 0))
            
            logger.info("State module enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable state module: {e}")
            return False
    
    def disable(self) -> bool:
        """Pause state machine operations"""
        logger.info("State module disabled")
        return True
    
    def shutdown(self) -> bool:
        """Cleanup state machine"""
        self.machine = None
        self.current_state_data = None
        logger.info("State module shutdown")
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle state transition requests"""
        try:
            if event_type == "state.transition.alert":
                message = event_data.get("message", "Alert")
                priority = event_data.get("priority", 2)
                metadata = event_data.get("metadata", {})
                self.transition_to_alert(message, priority, metadata)
                
            elif event_type == "state.transition.reminder":
                message = event_data.get("message", "Reminder")
                priority = event_data.get("priority", 1)
                metadata = event_data.get("metadata", {})
                self.transition_to_reminder(message, priority, metadata)
                
            elif event_type == "state.transition.scanning":
                self.transition_to_scanning()
                
            elif event_type == "state.transition.idle":
                self.transition_to_idle()
                
        except Exception as e:
            logger.error(f"Error handling state event '{event_type}': {e}")
    
    def _setup_transitions(self):
        """Setup state machine transitions"""
        # From IDLE
        self.machine.add_transition(
            trigger='start_scan',
            source=CompanionState.IDLE.value,
            dest=CompanionState.SCANNING.value,
            after='_on_enter_scanning'
        )
        self.machine.add_transition(
            trigger='trigger_alert',
            source=CompanionState.IDLE.value,
            dest=CompanionState.ALERT.value,
            after='_on_enter_alert'
        )
        self.machine.add_transition(
            trigger='show_reminder',
            source=CompanionState.IDLE.value,
            dest=CompanionState.REMINDER.value,
            after='_on_enter_reminder'
        )
        
        # From SCANNING
        self.machine.add_transition(
            trigger='finish_scan',
            source=CompanionState.SCANNING.value,
            dest=CompanionState.IDLE.value,
            after='_on_enter_idle'
        )
        self.machine.add_transition(
            trigger='trigger_alert',
            source=CompanionState.SCANNING.value,
            dest=CompanionState.ALERT.value,
            after='_on_enter_alert'
        )
        
        # From ALERT
        self.machine.add_transition(
            trigger='dismiss_alert',
            source=CompanionState.ALERT.value,
            dest=CompanionState.IDLE.value,
            after='_on_enter_idle'
        )
        
        # From REMINDER
        self.machine.add_transition(
            trigger='dismiss_reminder',
            source=CompanionState.REMINDER.value,
            dest=CompanionState.IDLE.value,
            after='_on_enter_idle'
        )
    
    # State entry callbacks
    def _on_enter_idle(self):
        """Enter idle state"""
        logger.info("Entering IDLE state")
        self._emit_state_change(CompanionState.IDLE, StateData("Idle mode", 0))
    
    def _on_enter_scanning(self):
        """Enter scanning state"""
        logger.info("Entering SCANNING state")
        self._emit_state_change(CompanionState.SCANNING, StateData("Scanning system", 1))
    
    def _on_enter_alert(self):
        """Enter alert state"""
        logger.warning("Entering ALERT state")
        if self.current_state_data:
            self._emit_state_change(CompanionState.ALERT, self.current_state_data)
    
    def _on_enter_reminder(self):
        """Enter reminder state"""
        logger.info("Entering REMINDER state")
        if self.current_state_data:
            self._emit_state_change(CompanionState.REMINDER, self.current_state_data)
    
    # Public transition methods
    def transition_to_alert(self, message: str, priority: int = 2, metadata: Optional[Dict[str, Any]] = None):
        """Transition to alert state with data"""
        self.current_state_data = StateData(message, priority, metadata)
        self.trigger_alert()
    
    def transition_to_reminder(self, message: str, priority: int = 1, metadata: Optional[Dict[str, Any]] = None):
        """Transition to reminder state with data"""
        self.current_state_data = StateData(message, priority, metadata)
        self.show_reminder()
    
    def transition_to_scanning(self):
        """Transition to scanning state"""
        self.start_scan()
    
    def transition_to_idle(self):
        """Transition to idle state"""
        if self.state == CompanionState.SCANNING.value:
            self.finish_scan()
        elif self.state == CompanionState.ALERT.value:
            self.dismiss_alert()
        elif self.state == CompanionState.REMINDER.value:
            self.dismiss_reminder()
    
    def _emit_state_change(self, state: CompanionState, data: StateData):
        """Emit state change event to event bus"""
        self.kernel.emit_event(self.name, "state.changed", {
            "state": state.value,
            "message": data.message,
            "priority": data.priority,
            "metadata": data.metadata,
            "timestamp": data.timestamp
        })
    
    def get_current_state(self) -> CompanionState:
        """Get current state"""
        return CompanionState(self.state)
    
    def get_state_data(self) -> Optional[StateData]:
        """Get current state data"""
        return self.current_state_data
