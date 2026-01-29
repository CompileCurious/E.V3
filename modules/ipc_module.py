"""
IPC Module
Handles inter-process communication with UI via named pipes
"""

from typing import Dict, Any, Set, Optional
from loguru import logger

from kernel.module import Module, Permission, KernelAPI
from ipc.native_pipe import IPCServer


class IPCModule(Module):
    """
    IPC capability module
    Manages communication with UI shell via named pipes
    Enforces permission boundaries on IPC messages
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("ipc", kernel_api)
        self.server: Optional[IPCServer] = None
    
    def get_required_permissions(self) -> Set[Permission]:
        """IPC module needs send/receive and event handling"""
        return {
            Permission.IPC_SEND,
            Permission.IPC_RECEIVE,
            Permission.EVENT_EMIT,
            Permission.EVENT_SUBSCRIBE,
            Permission.STORAGE_READ,
        }
    
    def get_dependencies(self) -> Set[str]:
        """Depends on state module"""
        return {"state"}
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize IPC server"""
        try:
            self.config = config
            ipc_config = config.get("ipc", {})
            
            pipe_name = ipc_config.get("pipe_name", r"\\.\pipe\E.V3.v2")
            buffer_size = ipc_config.get("buffer_size", 4096)
            
            self.server = IPCServer(pipe_name, buffer_size)
            
            # Register handlers
            self.server.register_handler("user_message", self._handle_user_message)
            self.server.register_handler("dismiss", self._handle_dismiss)
            
            logger.info("IPC module loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load IPC module: {e}")
            return False
    
    def enable(self) -> bool:
        """Start IPC server"""
        try:
            # Subscribe to state changes to relay to UI
            self.kernel.subscribe_event(self.name, "state.changed")
            
            # Subscribe to outbound IPC messages
            self.kernel.subscribe_event(self.name, "ipc.send_message")
            
            # Start IPC server
            if self.server:
                self.server.start()
            
            logger.info("IPC module enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable IPC module: {e}")
            return False
    
    def disable(self) -> bool:
        """Stop IPC server"""
        if self.server:
            self.server.stop()
        logger.info("IPC module disabled")
        return True
    
    def shutdown(self) -> bool:
        """Cleanup IPC resources"""
        self.disable()
        self.server = None
        logger.info("IPC module shutdown")
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle events for IPC transmission"""
        try:
            if event_type == "state.changed":
                # Forward state changes to UI
                self._send_state_update(event_data)
                
            elif event_type == "ipc.send_message":
                # Forward message to UI
                msg_type = event_data.get("type", "message")
                msg_data = event_data.get("data", {})
                if self.server:
                    self.server.send_message(msg_type, msg_data)
                
        except Exception as e:
            logger.error(f"Error handling IPC event '{event_type}': {e}")
    
    def _handle_user_message(self, data: Dict[str, Any]):
        """
        Handle incoming user message from UI
        Permission check: IPC_RECEIVE
        """
        message = data.get("message", "")
        logger.info(f"User message received: {message[:50]}...")
        
        # Check for external LLM trigger
        use_external = "find out" in message.lower()
        
        # Emit to LLM module for processing
        self.kernel.emit_event(self.name, "ipc.user_message", {
            "message": message,
            "use_external": use_external
        })
    
    def _handle_dismiss(self, data: Dict[str, Any]):
        """
        Handle dismiss action from UI
        Permission check: IPC_RECEIVE
        """
        logger.info("User dismissed notification")
        
        # Request state transition to idle
        self.kernel.emit_event(self.name, "state.transition.idle", {})
    
    def _send_state_update(self, state_data: Dict[str, Any]):
        """
        Send state update to UI
        Permission check: IPC_SEND (checked by kernel API)
        """
        if self.server:
            self.server.send_message("state_update", state_data)
