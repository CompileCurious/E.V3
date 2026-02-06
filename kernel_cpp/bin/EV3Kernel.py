#!/usr/bin/env python3
"""
E.V3 Quick Production Kernel - Lightweight IPC Server
Connects to Shell via Windows Named Pipes
Includes mock LLM for testing
"""

import json
import logging
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'kernel.log')
    ]
)
logger = logging.getLogger('EV3Kernel')

# ============================================================================
# Mock LLM - For immediate testing
# ============================================================================

class MockLLM:
    """Mock LLM that responds immediately for testing"""
    
    def __init__(self):
        self.mode = 'fast'
        
    def infer(self, prompt: str, max_tokens: int = 128) -> str:
        """Return mock LLM response"""
        try:
            # Check if actual llama-cpp is available
            try:
                from llama_cpp import Llama
                logger.info("Using real llama-cpp model")
                # Try to load a model
                model_path = Path(__file__).parent.parent.parent / 'models' / 'llm' / 'Phi-3-mini-4k-instruct-q4.gguf'
                if model_path.exists():
                    model = Llama(str(model_path), n_ctx=512, verbose=False)
                    response = model(prompt, max_tokens=max_tokens, temperature=0.7, stop=["\n"])
                    return response['choices'][0]['text'].strip()
            except:
                pass
            
            # Fallback to mock responses for different prompt types
            prompt_lower = prompt.lower()
            
            if any(x in prompt_lower for x in ['hello', 'hi', 'greeting', 'hey']):
                return "Hello! I'm E.V3, your AI assistant. How can I help you today?"
            elif any(x in prompt_lower for x in ['time', 'what time', 'current time']):
                return f"The current time is {datetime.now().strftime('%H:%M:%S')}"
            elif any(x in prompt_lower for x in ['date', 'today', 'what date']):
                return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            elif any(x in prompt_lower for x in ['name', 'who are you', 'introduce']):
                return "I'm E.V3, an advanced AI system running on Python and C++ technologies."
            elif any(x in prompt_lower for x in ['help', 'what can you do', 'capabilities']):
                return "I can help with conversations, answer questions, provide information, and assist with various tasks."
            else:
                # Generic response
                return f"I understand you're asking about '{prompt[:50]}...'. I'm here to help! Could you provide more details?"
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Error processing request: {str(e)}"
            
    def set_mode(self, mode: str):
        self.mode = mode

# ============================================================================
# IPC Server - Windows Named Pipes (Pure Python)
# ============================================================================

class IPCServer:
    """Windows Named Pipes IPC Server using Python socket emulation"""
    
    def __init__(self, pipe_name=r'\\.\pipe\E.V3.v2'):
        self.pipe_name = pipe_name
        self.running = False
        self.llm = MockLLM()
        
    def start(self):
        """Start IPC server"""
        self.running = True
        logger.info(f"Starting IPC Server on {self.pipe_name}")
        
        try:
            import win32pipe
            import win32file
            import pywintypes
        except ImportError:
            logger.error("pywin32 not available, trying alternative method...")
            self._start_socket_alternative()
            return
        
        while self.running:
            try:
                # Create named pipe
                try:
                    pipe = win32pipe.CreateNamedPipe(
                        self.pipe_name,
                        win32pipe.PIPE_ACCESS_DUPLEX,
                        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE,
                        1, 65536, 65536, 0, None
                    )
                except pywintypes.error as e:
                    if self.running:
                        logger.debug(f"CreateNamedPipe: {e}, retrying...")
                        time.sleep(1)
                    continue
                
                logger.info("Waiting for Shell connection...")
                try:
                    win32pipe.ConnectNamedPipe(pipe, None)
                except pywintypes.error as e:
                    logger.debug(f"ConnectNamedPipe: {e}")
                    continue
                
                logger.info("[OK] Shell connected via IPC")
                
                # Handle client communication
                try:
                    while self.running:
                        try:
                            hr, data = win32file.ReadFile(pipe, 4096)
                            if not data:
                                break
                            
                            message = data.decode('utf-8', errors='ignore').strip()
                            if message:
                                logger.debug(f"Received: {message[:100]}")
                                response = self.handle_message(message)
                                logger.debug(f"Sending: {response[:100]}")
                                win32file.WriteFile(pipe, response.encode('utf-8'))
                        except (OSError, IOError):
                            break
                finally:
                    try:
                        win32file.CloseHandle(pipe)
                    except:
                        pass
                    logger.info("Shell disconnected")
                    
            except Exception as e:
                logger.error(f"Server error: {e}")
                if self.running:
                    time.sleep(1)
                    
    def _start_socket_alternative(self):
        """Fallback socket-based IPC"""
        import socket
        logger.warning("Using socket-based IPC instead of named pipes")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 9999))
        sock.listen(1)
        
        while self.running:
            try:
                conn, addr = sock.accept()
                logger.info(f"Client connected from {addr}")
                
                while self.running:
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break
                        
                        message = data.decode('utf-8', errors='ignore').strip()
                        if message:
                            response = self.handle_message(message)
                            conn.send(response.encode('utf-8'))
                    except Exception:
                        break
                        
                conn.close()
            except Exception as e:
                if self.running:
                    logger.error(f"Socket error: {e}")
    
    def handle_message(self, message: str) -> str:
        """Process IPC message and return response"""
        try:
            data = json.loads(message)
            command = data.get('command', 'ping')
            
            if command == 'ping':
                return json.dumps({
                    'command': 'ping',
                    'response': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
            
            elif command == 'status':
                return json.dumps({
                    'command': 'status',
                    'status': 'online',
                    'kernel': 'EV3-Python',
                    'version': '2.0.0',
                    'timestamp': datetime.now().isoformat()
                })
            
            elif command == 'infer':
                prompt = data.get('prompt', 'Hello')
                max_tokens = data.get('max_tokens', 128)
                result = self.llm.infer(prompt, max_tokens)
                return json.dumps({
                    'command': 'infer',
                    'prompt': prompt,
                    'response': result,
                    'status': 'ok'
                })
            
            elif command == 'mode':
                mode = data.get('mode', 'fast')
                self.llm.set_mode(mode)
                return json.dumps({
                    'command': 'mode',
                    'mode': mode,
                    'status': 'ok'
                })
            
            else:
                return json.dumps({
                    'error': f'Unknown command: {command}',
                    'status': 'error'
                })
                
        except json.JSONDecodeError:
            return json.dumps({
                'error': 'Invalid JSON',
                'status': 'error'
            })
        except Exception as e:
            logger.error(f"Message handling error: {e}\n{traceback.format_exc()}")
            return json.dumps({
                'error': str(e),
                'status': 'error'
            })

# ============================================================================
# Kernel
# ============================================================================

class EV3Kernel:
    """Main E.V3 Kernel"""
    
    def __init__(self):
        self.ipc_server = IPCServer()
        self.running = False
        
    def start(self):
        """Start kernel"""
        self.running = True
        logger.info("="*70)
        logger.info("E.V3 KERNEL v2.0.0 - Python Production Build")
        logger.info("="*70)
        logger.info("Status: Starting...")
        logger.info("Mode: Quick-Start with Mock LLM")
        logger.info("IPC: Windows Named Pipes")
        logger.info("="*70)
        
        # Start IPC server
        ipc_thread = threading.Thread(target=self.ipc_server.start, daemon=True)
        ipc_thread.start()
        
        # Keep kernel alive
        try:
            logger.info("[OK] Kernel ready - waiting for Shell connection...")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
            self.stop()
            
    def stop(self):
        """Stop kernel"""
        self.running = False
        self.ipc_server.running = False
        logger.info("[OK] Kernel stopped")

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    try:
        # Ensure logs directory exists
        (Path(__file__).parent.parent / 'logs').mkdir(exist_ok=True)
        
        kernel = EV3Kernel()
        kernel.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
