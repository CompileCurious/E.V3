"""
Native Windows IPC using Named Pipes
Fast, secure, local-only communication between service and UI
"""

import win32pipe
import win32file
import win32event
import pywintypes
import json
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue
from loguru import logger


class IPCServer:
    """
    IPC Server using Windows Named Pipes
    Privacy: All communication is local-only, never leaves the machine
    """
    
    def __init__(self, pipe_name: str = r"\\.\pipe\E.V3", buffer_size: int = 4096):
        self.pipe_name = pipe_name
        self.buffer_size = buffer_size
        self.pipe_handle: Optional[int] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._message_handlers: Dict[str, Callable] = {}
        self._outbound_queue: Queue = Queue()
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self._message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def start(self):
        """Start the IPC server"""
        if self.running:
            logger.warning("IPC server already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        logger.info(f"IPC server started on {self.pipe_name}")
    
    def stop(self):
        """Stop the IPC server"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
            except:
                pass
        logger.info("IPC server stopped")
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        """Queue a message to send to client"""
        message = {
            "type": message_type,
            "data": data
        }
        self._outbound_queue.put(message)
    
    def _run_server(self):
        """Main server loop"""
        while self.running:
            try:
                # Create named pipe
                self.pipe_handle = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    self.buffer_size,
                    self.buffer_size,
                    0,  # Default timeout
                    None
                )
                
                logger.debug("Waiting for client connection...")
                
                # Wait for client to connect
                win32pipe.ConnectNamedPipe(self.pipe_handle, None)
                logger.info("Client connected")
                
                # Handle communication
                self._handle_client()
                
            except pywintypes.error as e:
                if self.running:
                    logger.error(f"Pipe error: {e}")
            except Exception as e:
                if self.running:
                    logger.error(f"Server error: {e}")
            finally:
                if self.pipe_handle:
                    try:
                        win32file.CloseHandle(self.pipe_handle)
                    except:
                        pass
                    self.pipe_handle = None
    
    def _handle_client(self):
        """Handle client communication"""
        while self.running:
            try:
                # Read from client
                result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
                if data:
                    message = json.loads(data.decode('utf-8'))
                    self._process_message(message)
                
                # Send queued messages to client
                while not self._outbound_queue.empty():
                    msg = self._outbound_queue.get()
                    self._send_to_client(msg)
                    
            except pywintypes.error as e:
                # Client disconnected
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Client handling error: {e}")
                break
    
    def _send_to_client(self, message: Dict[str, Any]):
        """Send message to client"""
        try:
            data = json.dumps(message).encode('utf-8')
            win32file.WriteFile(self.pipe_handle, data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    def _process_message(self, message: Dict[str, Any]):
        """Process received message"""
        try:
            msg_type = message.get("type")
            msg_data = message.get("data", {})
            
            if msg_type in self._message_handlers:
                self._message_handlers[msg_type](msg_data)
            else:
                logger.warning(f"No handler for message type: {msg_type}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")


class IPCClient:
    """
    IPC Client using Windows Named Pipes
    Privacy: All communication is local-only
    """
    
    def __init__(self, pipe_name: str = r"\\.\pipe\E.V3", buffer_size: int = 4096):
        self.pipe_name = pipe_name
        self.buffer_size = buffer_size
        self.pipe_handle: Optional[int] = None
        self.connected = False
        self._message_handlers: Dict[str, Callable] = {}
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self._message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def connect(self, timeout_ms: int = 5000) -> bool:
        """Connect to the IPC server"""
        try:
            # Wait for pipe to be available
            win32pipe.WaitNamedPipe(self.pipe_name, timeout_ms)
            
            # Open the pipe
            self.pipe_handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            
            # Set pipe mode
            win32pipe.SetNamedPipeHandleState(
                self.pipe_handle,
                win32pipe.PIPE_READMODE_MESSAGE,
                None,
                None
            )
            
            self.connected = True
            
            # Start listening thread
            self._running = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()
            
            logger.info("Connected to IPC server")
            return True
            
        except pywintypes.error as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self._running = False
        self.connected = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
            except:
                pass
        logger.info("Disconnected from IPC server")
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        """Send message to server"""
        if not self.connected:
            logger.warning("Not connected to server")
            return
        
        try:
            message = {
                "type": message_type,
                "data": data
            }
            msg_data = json.dumps(message).encode('utf-8')
            win32file.WriteFile(self.pipe_handle, msg_data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    def _listen(self):
        """Listen for messages from server"""
        while self._running and self.connected:
            try:
                result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
                if data:
                    message = json.loads(data.decode('utf-8'))
                    self._process_message(message)
            except pywintypes.error:
                # Connection lost
                logger.info("Connection to server lost")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"Listen error: {e}")
    
    def _process_message(self, message: Dict[str, Any]):
        """Process received message"""
        try:
            msg_type = message.get("type")
            msg_data = message.get("data", {})
            
            if msg_type in self._message_handlers:
                self._message_handlers[msg_type](msg_data)
            else:
                logger.debug(f"No handler for message type: {msg_type}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
