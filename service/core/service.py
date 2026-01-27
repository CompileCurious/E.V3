"""
E.V3 Core Service
Background service that coordinates all components
Privacy: All data processing happens locally
"""

import yaml
from loguru import logger
from typing import Dict, Any, Optional
import sys
import signal
from pathlib import Path

from service.state import CompanionStateMachine, CompanionState, StateData
from service.events import EventManager
from service.llm import LLMManager
from service.calendar import CalendarManager, CalendarEvent
from ipc import IPCServer


class EV3Service:
    """
    Main E.V3 service
    Coordinates state machine, event monitoring, LLM, calendar, and UI communication
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.state_machine: Optional[CompanionStateMachine] = None
        self.event_manager: Optional[EventManager] = None
        self.llm_manager: Optional[LLMManager] = None
        self.calendar_manager: Optional[CalendarManager] = None
        self.ipc_server: Optional[IPCServer] = None
        
        self.running = False
        
        logger.info("E.V3 Service initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )
        
        # Add file handler if enabled
        if log_config.get("log_to_file", True):
            log_file = log_config.get("log_file", "logs/ev3.log")
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                level=log_level,
                rotation=log_config.get("max_file_size", 10485760),
                retention=log_config.get("backup_count", 5),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
            )
        
        logger.info("Logging configured")
    
    def initialize(self):
        """Initialize all service components"""
        logger.info("Initializing E.V3 service components...")
        
        # Initialize state machine
        self.state_machine = CompanionStateMachine(self.config)
        self.state_machine.register_state_callback(
            CompanionState.ALERT,
            self._on_alert_state
        )
        self.state_machine.register_state_callback(
            CompanionState.REMINDER,
            self._on_reminder_state
        )
        
        # Initialize IPC server
        ipc_config = self.config.get("ipc", {})
        self.ipc_server = IPCServer(
            pipe_name=ipc_config.get("pipe_name", r"\\.\pipe\E.V3"),
            buffer_size=ipc_config.get("buffer_size", 4096)
        )
        
        # Register IPC message handlers
        self.ipc_server.register_handler("user_message", self._handle_user_message)
        self.ipc_server.register_handler("dismiss", self._handle_dismiss)
        
        # Initialize LLM manager
        self.llm_manager = LLMManager(self.config)
        
        # Initialize event manager
        self.event_manager = EventManager(self.config)
        
        # Register event callbacks
        self.event_manager.register_callback("defender", self._on_defender_event)
        self.event_manager.register_callback("firewall", self._on_firewall_event)
        self.event_manager.register_callback("system", self._on_system_event)
        
        # Initialize calendar manager
        if self.config.get("calendar", {}).get("enabled", True):
            self.calendar_manager = CalendarManager(self.config)
            self.calendar_manager.register_reminder_callback(self._on_calendar_reminder)
        
        logger.info("All components initialized")
    
    def start(self):
        """Start the service"""
        if self.running:
            logger.warning("Service already running")
            return
        
        logger.info("Starting E.V3 service...")
        self.running = True
        
        # Start IPC server
        self.ipc_server.start()
        
        # Start event monitoring
        self.event_manager.start_all()
        
        # Start calendar monitoring
        if self.calendar_manager:
            self.calendar_manager.start()
        
        # Send initial state to UI
        self._send_state_update(CompanionState.IDLE, StateData("Ready", 0))
        
        logger.info("E.V3 service started successfully")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Keep running
        try:
            signal.pause()
        except AttributeError:
            # Windows doesn't have signal.pause()
            import time
            while self.running:
                time.sleep(1)
    
    def stop(self):
        """Stop the service"""
        logger.info("Stopping E.V3 service...")
        self.running = False
        
        # Stop all components
        if self.calendar_manager:
            self.calendar_manager.stop()
        
        if self.event_manager:
            self.event_manager.stop_all()
        
        if self.ipc_server:
            self.ipc_server.stop()
        
        logger.info("E.V3 service stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    # Event handlers
    def _on_defender_event(self, event_data: Dict[str, Any]):
        """Handle Windows Defender event"""
        logger.info(f"Defender event: {event_data}")
        
        # Interpret event with LLM
        interpretation = self.llm_manager.interpret_event(event_data)
        
        # Determine priority
        priority = 2 if event_data.get("threat_detected") else 1
        
        # Transition to alert state
        self.state_machine.transition_to_alert(
            interpretation,
            priority=priority,
            metadata=event_data
        )
    
    def _on_firewall_event(self, event_data: Dict[str, Any]):
        """Handle firewall event"""
        logger.info(f"Firewall event: {event_data}")
        
        interpretation = self.llm_manager.interpret_event(event_data)
        
        self.state_machine.transition_to_alert(
            interpretation,
            priority=1,
            metadata=event_data
        )
    
    def _on_system_event(self, event_data: Dict[str, Any]):
        """Handle system event"""
        logger.info(f"System event: {event_data}")
        
        interpretation = self.llm_manager.interpret_event(event_data)
        
        self.state_machine.transition_to_alert(
            interpretation,
            priority=1,
            metadata=event_data
        )
    
    def _on_calendar_reminder(self, event: CalendarEvent):
        """Handle calendar reminder"""
        logger.info(f"Calendar reminder: {event.title}")
        
        message = f"Reminder: {event.title} in {int(event.time_until_start() / 60)} minutes"
        
        self.state_machine.transition_to_reminder(
            message,
            priority=1,
            metadata={"event": event.title, "time": event.start_time.isoformat()}
        )
    
    # State callbacks
    def _on_alert_state(self, state: CompanionState, data: StateData):
        """Handle alert state"""
        self._send_state_update(state, data)
    
    def _on_reminder_state(self, state: CompanionState, data: StateData):
        """Handle reminder state"""
        self._send_state_update(state, data)
    
    # IPC handlers
    def _handle_user_message(self, data: Dict[str, Any]):
        """Handle message from user via UI"""
        message = data.get("message", "")
        logger.info(f"User message: {message}")
        
        # Process with LLM
        response = self.llm_manager.process_query(message)
        
        # Send response to UI
        self.ipc_server.send_message("llm_response", {
            "message": response
        })
    
    def _handle_dismiss(self, data: Dict[str, Any]):
        """Handle dismiss action from UI"""
        logger.info("User dismissed notification")
        self.state_machine.transition_to_idle()
    
    def _send_state_update(self, state: CompanionState, data: StateData):
        """Send state update to UI"""
        if self.ipc_server:
            self.ipc_server.send_message("state_update", {
                "state": state.value,
                "message": data.message,
                "priority": data.priority,
                "timestamp": data.timestamp
            })


def main():
    """Main entry point"""
    logger.info("Starting E.V3 Privacy-Focused Desktop Companion")
    
    # Create and start service
    service = EV3Service()
    service.initialize()
    service.start()


if __name__ == "__main__":
    main()
