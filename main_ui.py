"""
E.V3 UI Application
Connects to background service via IPC and displays 3D companion
"""

import sys
import yaml
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Signal, QObject
from loguru import logger

from ui.window import CompanionWindow
from ui.speech import SpeechManager
from ipc import IPCClient


def check_single_instance():
    """Ensure only one instance of the Shell is running"""
    mutex_name = "Global\\EV3ShellMutex"
    mutex = win32event.CreateMutex(None, True, mutex_name)  # Changed to True to immediately acquire
    last_error = win32api.GetLastError()
    
    if last_error == ERROR_ALREADY_EXISTS:
        logger.warning("E.V3 Shell is already running. Exiting.")
        return None  # Return None instead of False
    
    return mutex  # Return the mutex handle to keep it alive


class EV3UIApplication(QObject):
    """
    Main UI application
    - Displays 3D companion window
    - Connects to background kernel via IPC
    - Updates UI based on kernel state
    """
    # Signal to safely deliver LLM responses from IPC thread to UI thread
    llm_response_signal = Signal(str)
    
    def __init__(self, config_path: str = "config/config.yaml"):
        super().__init__()
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
        
        # Speech manager
        self.speech_manager: SpeechManager = None
        
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
        
        # Initialize speech manager
        self.speech_manager = SpeechManager(self.config)
        
        # Create main window
        self.window = CompanionWindow(self.config)
        
        # Connect the signal to deliver LLM responses
        self.llm_response_signal.connect(self._deliver_llm_response)
        
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
        
        self.ipc_client.register_handler("speak", self._handle_speak)
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
        
        # Show window at startup for testing
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
        """Handle LLM response from service (called from IPC thread)"""
        message = data.get("message", "")
        
        logger.info(f"LLM response received: {message[:100]}...")
        logger.info(f"Window object: {self.window}, has chat_window: {hasattr(self.window, 'chat_window') if self.window else False}")
        
        # Emit signal to deliver response on UI thread
        logger.info("Emitting llm_response_signal")
        self.llm_response_signal.emit(message)
        logger.info("Signal emitted")
    
    def _deliver_llm_response(self, message: str):
        """Deliver LLM response to UI (runs on UI thread via signal)"""
        logger.info("_deliver_llm_response called on UI thread")
        try:
            if self.window:
                logger.info(f"Calling display_chat_response with message length: {len(message)}")
                self.window.display_chat_response(message)
                logger.info("display_chat_response completed")
            else:
                logger.warning("No window available to display response")
        except Exception as e:
            logger.error(f"Error delivering LLM response to UI: {e}", exc_info=True)
    
    def _send_message_via_ipc(self, message: str):
        """Send user message to kernel via IPC"""
        if self.ipc_client and self.ipc_client.connected:
            logger.info(f"Sending message to kernel: {message[:50]}...")
            self.ipc_client.send_message("user_message", {"message": message})
        else:
            logger.warning("IPC client not connected")
    
    def _handle_speak(self, data):
        """
        Handle speech request from kernel
        
        Expected data format:
        {
            "text": "Hello, how are you?",
            "emotion": "happy",  # optional
            "blocking": false    # optional
        }
        """
        text = data.get("text", "")
        emotion = data.get("emotion", "neutral")
        blocking = data.get("blocking", False)
        
        if not text:
            logger.warning("Received speak message with no text")
            return
        
        logger.info(f"Speak request: '{text}' [emotion: {emotion}]")
        
        # Generate and play speech
        if self.speech_manager:
            result = self.speech_manager.speak(text, emotion, blocking)
            
            if result:
                # Update animation system with phoneme data
                if hasattr(self.window, 'sync_speech_animation'):
                    self.window.sync_speech_animation(result)
                
                logger.debug(f"Speech playback initiated: {result.get('duration', 0):.2f}s")
            else:
                logger.warning("Speech generation failed")
        else:
            logger.warning("Speech manager not initialized")
    
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
    # Check for single instance before any UI initialization and keep mutex handle
    mutex = check_single_instance()
    if mutex is None:
        # Show message box if possible
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "E.V3 Shell Already Running",
            "E.V3 Shell is already running.\n\nPlease check your system tray for the E.V3 icon.",
            QMessageBox.Ok
        )
        logger.warning("Exiting - Shell instance already running")
        sys.exit(1)
    
    logger.info("Starting E.V3 Desktop Companion UI")
    
    # Create and run application
    app = EV3UIApplication()
    app.initialize()
    app.run()


if __name__ == "__main__":
    main()
