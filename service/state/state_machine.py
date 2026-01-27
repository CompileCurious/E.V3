"""
State Machine for E.V3 Companion

States:
- idle: Normal state, light monitoring
- scanning: Active monitoring of events
- alert: Important security/system event detected
- reminder: Calendar reminder active
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any
from transitions import Machine
from loguru import logger
import time


class CompanionState(Enum):
    """Companion states"""
    IDLE = "idle"
    SCANNING = "scanning"
    ALERT = "alert"
    REMINDER = "reminder"


class StateData:
    """Data associated with state transitions"""
    def __init__(self, message: str = "", priority: int = 0, metadata: Optional[Dict[str, Any]] = None):
        self.message = message
        self.priority = priority  # 0=low, 1=medium, 2=high, 3=critical
        self.metadata = metadata or {}
        self.timestamp = time.time()


class CompanionStateMachine:
    """
    State machine for the companion service
    Privacy: All state data is kept local and never sent externally
    """
    
    # Define states
    states = [
        CompanionState.IDLE.value,
        CompanionState.SCANNING.value,
        CompanionState.ALERT.value,
        CompanionState.REMINDER.value,
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_state_data: Optional[StateData] = None
        self._state_callbacks: Dict[str, list] = {state: [] for state in self.states}
        
        # Initialize the state machine
        self.machine = Machine(
            model=self,
            states=CompanionStateMachine.states,
            initial=CompanionState.IDLE.value,
            auto_transitions=False
        )
        
        # Define transitions
        self._setup_transitions()
        
        logger.info("State machine initialized")
    
    def _setup_transitions(self):
        """Setup state transitions"""
        
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
        
        logger.debug("State transitions configured")
    
    # State entry callbacks
    def _on_enter_idle(self):
        """Enter idle state"""
        logger.info("Entering IDLE state")
        self._notify_state_change(CompanionState.IDLE, StateData("Idle mode", 0))
    
    def _on_enter_scanning(self):
        """Enter scanning state"""
        logger.info("Entering SCANNING state")
        self._notify_state_change(CompanionState.SCANNING, StateData("Scanning system", 1))
    
    def _on_enter_alert(self):
        """Enter alert state"""
        logger.warning("Entering ALERT state")
        if self.current_state_data:
            self._notify_state_change(CompanionState.ALERT, self.current_state_data)
    
    def _on_enter_reminder(self):
        """Enter reminder state"""
        logger.info("Entering REMINDER state")
        if self.current_state_data:
            self._notify_state_change(CompanionState.REMINDER, self.current_state_data)
    
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
    
    def register_state_callback(self, state: CompanionState, callback: Callable):
        """Register a callback for state changes"""
        self._state_callbacks[state.value].append(callback)
        logger.debug(f"Registered callback for {state.value}")
    
    def _notify_state_change(self, state: CompanionState, data: StateData):
        """Notify all registered callbacks of state change"""
        for callback in self._state_callbacks[state.value]:
            try:
                callback(state, data)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def get_current_state(self) -> CompanionState:
        """Get current state as enum"""
        return CompanionState(self.state)
    
    def get_state_data(self) -> Optional[StateData]:
        """Get current state data"""
        return self.current_state_data
