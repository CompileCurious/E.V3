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
import time
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
        import time
        while self.running:
            try:
                # Create named pipe
                self.pipe_handle = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    5,  # Max instances (increased to avoid "all instances busy")
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
                    # Wait before retry to avoid tight loop on persistent errors
                    time.sleep(2.0)
            except Exception as e:
                if self.running:
                    logger.error(f"Server error: {e}")
                    time.sleep(2.0)
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
                # Check if data is available without blocking
                try:
                    # Peek to see if there's data
                    result = win32pipe.PeekNamedPipe(self.pipe_handle, 0)
                    if result[1] > 0:  # bytes available
                        # Read from client
                        result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            self._process_message(message)
                except pywintypes.error as e:
                    # Check if it's a disconnect
                    if e.winerror == 109:  # ERROR_BROKEN_PIPE
                        logger.info("Client disconnected")
                        break
                    # Otherwise continue - might be no data available
                
                # Send queued messages to client
                while not self._outbound_queue.empty():
                    msg = self._outbound_queue.get()
                    self._send_to_client(msg)
                
                # Small sleep to avoid busy loop
                time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Client handling error: {e}", exc_info=True)
                break
    
    def _send_to_client(self, message: Dict[str, Any]):
        """Send message to client"""
        try:
            msg_type = message.get("type", "unknown")
            logger.info(f"Sending message to client: type='{msg_type}'")
            data = json.dumps(message).encode('utf-8')
            win32file.WriteFile(self.pipe_handle, data)
            logger.info(f"Message sent successfully")
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
        self._outbound_queue: Queue = Queue()  # Queue for messages to send
    
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
            # Use debug level to avoid spamming logs during retries
            logger.debug(f"Failed to connect to IPC server: {e}")
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
        """Queue a message to send to server"""
        message = {
            "type": message_type,
            "data": data
        }
        self._outbound_queue.put(message)
    
    def _listen(self):
        """Listen for messages from server and send queued outbound messages"""
        while self._running and self.connected:
            try:
                # Check for incoming messages (non-blocking peek)
                try:
                    result = win32pipe.PeekNamedPipe(self.pipe_handle, 0)
                    if result[1] > 0:  # bytes available
                        result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            logger.info(f"Client received message: {message.get('type')}")
                            self._process_message(message)
                except pywintypes.error as e:
                    if e.winerror == 109:  # ERROR_BROKEN_PIPE
                        logger.info("Connection to server lost")
                        self.connected = False
                        break
                
                # Send queued outbound messages
                while not self._outbound_queue.empty() and self.connected:
                    msg = self._outbound_queue.get()
                    try:
                        msg_data = json.dumps(msg).encode('utf-8')
                        win32file.WriteFile(self.pipe_handle, msg_data)
                        logger.debug(f"Client sent message: {msg.get('type')}")
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        self.connected = False
                        break
                
                # Small sleep to avoid busy loop
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Listen error: {e}", exc_info=True)
                self.connected = False
                break
    
    def _process_message(self, message: Dict[str, Any]):
        """Process received message"""
        try:
            msg_type = message.get("type")
            msg_data = message.get("data", {})
            
            logger.info(f"Processing message type '{msg_type}'")
            
            if msg_type in self._message_handlers:
                try:
                    self._message_handlers[msg_type](msg_data)
                    logger.info(f"Handler for '{msg_type}' completed")
                except Exception as e:
                    logger.error(f"Error in handler for '{msg_type}': {e}", exc_info=True)
            else:
                logger.warning(f"No handler registered for message type: {msg_type}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
