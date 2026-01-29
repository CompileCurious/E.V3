"""
E.V3 UI Application
Connects to background service via IPC and displays 3D companion
"""

import sys
import yaml
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from loguru import logger

from ui.window import CompanionWindow
from ipc import IPCClient


class EV3UIApplication:
    """
    Main UI application
    - Displays 3D companion window
    - Connects to background kernel via IPC
    - Updates UI based on kernel state
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("E.V3 Shell")
        self.app.setQuitOnLastWindowClosed(False)  # Don't quit when hiding to tray
        
        # Main window
        self.window: CompanionWindow = None
        
        # IPC client
        self.ipc_client: IPCClient = None
        
        logger.info("E.V3 UI Application initialized")
    
    def _load_config(self, config_path: str):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _setup_logging(self):
        """Setup logging"""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        
        logger.remove()
        
        # Add console handler only if stderr is available (not None in executables)
        if sys.stderr is not None:
            logger.add(
                sys.stderr,
                level=log_level,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
            )
        
        if log_config.get("log_to_file", True):
            log_file = "logs/ev3_ui.log"
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            logger.add(log_file, level=log_level)
    
    def initialize(self):
        """Initialize UI components"""
        logger.info("Initializing UI...")
        
        # Create main window
        self.window = CompanionWindow(self.config)
        
        # Connect chat message signal
        if hasattr(self.window, 'send_chat_message'):
            # Override the send_chat_message method to use IPC
            self.window.send_chat_message = self._send_message_via_ipc
        
        # Setup IPC client
        ipc_config = self.config.get("ipc", {})
        self.ipc_client = IPCClient(
            pipe_name=ipc_config.get("pipe_name", r"\\.\pipe\E.V3"),
            buffer_size=ipc_config.get("buffer_size", 4096)
        )
        
        # Register IPC handlers
        self.ipc_client.register_handler("state_update", self._handle_state_update)
        self.ipc_client.register_handler("llm_response", self._handle_llm_response)
        
        # Connect to service
        self._connect_to_service()
        
        logger.info("UI initialized")
    
    def _connect_to_service(self):
        """Connect to background kernel"""
        logger.info("Connecting to kernel...")
        
        # Try to connect
        if self.ipc_client.connect(timeout_ms=5000):
            logger.info("Connected to kernel")
        else:
            logger.warning("Failed to connect to kernel. UI will run in standalone mode.")
            logger.info("Start the kernel with: python main_service.py")
            
            # Retry connection periodically
            self.retry_timer = QTimer()
            self.retry_timer.timeout.connect(self._retry_connection)
            self.retry_timer.start(5000)  # Retry every 5 seconds
    
    def _retry_connection(self):
        """Retry connection to kernel"""
        if not self.ipc_client.connected:
            logger.debug("Retrying connection to kernel...")
            if self.ipc_client.connect(timeout_ms=1000):
                logger.info("Connected to kernel")
                self.retry_timer.stop()
        else:
            self.retry_timer.stop()
    
    def run(self):
        """Run the application"""
        logger.info("Starting E.V3 UI...")
        
        # Show window
        self.window.show()
        
        # Run Qt event loop
        sys.exit(self.app.exec())
    
    # IPC Message Handlers
    
    def _handle_state_update(self, data):
        """Handle state update from service"""
        state = data.get("state", "idle")
        message = data.get("message", "")
        priority = data.get("priority", 0)
        
        logger.info(f"State update: {state} - {message}")
        
        # Update window
        self.window.set_state(state, message, priority)
    
    def _handle_llm_response(self, data):
        """Handle LLM response from service"""
        message = data.get("message", "")
        
        logger.info(f"LLM response: {message}")
        
        # Display in chat window if open
        if self.window:
            self.window.display_chat_response(message)
            self.window.show_message(message)
    
    def _send_message_via_ipc(self, message: str):
        """Send user message to kernel via IPC"""
        if self.ipc_client and self.ipc_client.connected:
            logger.info(f"Sending message to kernel: {message[:50]}...")
            self.ipc_client.send_message("user_message", {"message": message})
        else:
            logger.warning("IPC client not connected")
    
    def send_user_message(self, message: str):
        """Send user message to service"""
        if self.ipc_client.connected:
            self.ipc_client.send_message("user_message", {"message": message})
        else:
            logger.warning("Cannot send message - not connected to service")
    
    def dismiss_notification(self):
        """Dismiss current notification"""
        if self.ipc_client.connected:
            self.ipc_client.send_message("dismiss", {})


def main():
    """Main entry point"""
    logger.info("Starting E.V3 Desktop Companion UI")
    
    # Create and run application
    app = EV3UIApplication()
    app.initialize()
    app.run()


if __name__ == "__main__":
    main()
