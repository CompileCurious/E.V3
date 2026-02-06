#!/usr/bin/env python3
"""
E.V3 Production Kernel - Full-Featured Implementation
Connects to Shell via Windows Named Pipes
Implements all C++ kernel features in Python for immediate functionality
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent / 'kernel.log')
    ]
)
logger = logging.getLogger('EV3Kernel')

# ============================================================================
# IPC Server - Windows Named Pipes
# ============================================================================

class IPCServer:
    """Windows Named Pipes IPC Server"""
    
    def __init__(self, pipe_name=r'\\.\pipe\E.V3.v2'):
        self.pipe_name = pipe_name
        self.running = False
        
    def start(self):
        """Start IPC server"""
        self.running = True
        logger.info(f"IPC Server listening on {self.pipe_name}")
        
        # Windows Named Pipes handling
        import win32pipe
        import win32file
        import pywintypes
        
        while self.running:
            try:
                # Create named pipe
                pipe = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE,
                    1, 65536, 65536, 0, None
                )
                
                logger.info("Waiting for client connection...")
                win32pipe.ConnectNamedPipe(pipe, None)
                logger.info("Client connected")
                
                # Handle client
                try:
                    while True:
                        hr, data = win32file.ReadFile(pipe, 4096)
                        if not data:
                            break
                        
                        message = data.decode('utf-8').strip()
                        logger.info(f"Received: {message}")
                        
                        # Process message
                        response = self.handle_message(message)
                        logger.info(f"Sending: {response}")
                        
                        win32file.WriteFile(pipe, response.encode('utf-8'))
                        
                except Exception as e:
                    logger.error(f"Error handling client: {e}")
                finally:
                    win32file.CloseHandle(pipe)
                    
            except pywintypes.error as e:
                if self.running:
                    logger.error(f"Pipe error: {e}")
                    time.sleep(1)
                    
    def handle_message(self, message: str) -> str:
        """Process IPC message and return response"""
        try:
            data = json.loads(message)
            command = data.get('command', '')
            
            if command == 'ping':
                return json.dumps({'status': 'pong', 'timestamp': datetime.now().isoformat()})
            elif command == 'status':
                return json.dumps({
                    'status': 'online',
                    'kernel': 'EV3-Python-Production',
                    'version': '2.0.0',
                    'timestamp': datetime.now().isoformat()
                })
            elif command == 'infer':
                # LLM inference
                prompt = data.get('prompt', '')
                result = kernel.llm_engine.infer(prompt)
                return json.dumps({'response': result, 'status': 'ok'})
            elif command == 'mode':
                # Set/get LLM mode
                mode = data.get('mode', 'fast')
                kernel.llm_engine.set_mode(mode)
                return json.dumps({'mode': mode, 'status': 'ok'})
            else:
                return json.dumps({'error': f'Unknown command: {command}'})
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON error: {e}")
            return json.dumps({'error': 'Invalid JSON'})
        except Exception as e:
            logger.error(f"Error: {e}\n{traceback.format_exc()}")
            return json.dumps({'error': str(e)})

# ============================================================================
# LLM Engine - Mistral/Phi-3 Support
# ============================================================================

class LLMEngine:
    """LLM inference engine supporting Mistral and Phi-3"""
    
    def __init__(self):
        self.mode = 'fast'  # 'fast' or 'deep'
        self.model = None
        self.model_name = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Load LLM model"""
        try:
            from llama_cpp import Llama
            
            # Try to load model
            models_dir = Path(__file__).parent.parent.parent / 'models' / 'llm'
            
            # Try Phi-3 first (smaller, faster)
            phi_path = models_dir / 'Phi-3-mini-4k-instruct-q4.gguf'
            mistral_path = models_dir / 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'
            
            if phi_path.exists():
                logger.info(f"Loading {phi_path}")
                self.model = Llama(str(phi_path), n_ctx=512, n_gpu_layers=0, verbose=False)
                self.model_name = 'Phi-3-mini'
            elif mistral_path.exists():
                logger.info(f"Loading {mistral_path}")
                self.model = Llama(str(mistral_path), n_ctx=512, n_gpu_layers=0, verbose=False)
                self.model_name = 'Mistral-7B'
            else:
                logger.warning(f"No models found in {models_dir}")
                self.model = None
                
        except ImportError:
            logger.warning("llama-cpp-python not installed, installing...")
            os.system(f'{sys.executable} -m pip install llama-cpp-python -q')
            self._initialize_model()
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            self.model = None
            
    def set_mode(self, mode: str):
        """Set LLM mode: 'fast' or 'deep'"""
        if mode in ['fast', 'deep']:
            self.mode = mode
            logger.info(f"LLM mode set to: {mode}")
            
    def infer(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Run LLM inference"""
        if not self.model:
            return "LLM model not loaded"
            
        try:
            if not max_tokens:
                max_tokens = 128 if self.mode == 'fast' else 256
                
            logger.info(f"Inferring ({self.mode}): {prompt[:50]}...")
            
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.95,
                stop=["\n"]
            )
            
            text = response['choices'][0]['text'].strip()
            logger.info(f"Response: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return f"Error: {str(e)}"

# ============================================================================
# Module System - Calendar, Events, System
# ============================================================================

class ModuleSystem:
    """Module system for extensibility"""
    
    def __init__(self):
        self.modules = {}
        self._load_modules()
        
    def _load_modules(self):
        """Load available modules"""
        # Calendar module
        try:
            from datetime import datetime
            self.modules['calendar'] = {
                'name': 'Calendar Module',
                'get_current_date': lambda: datetime.now().strftime('%Y-%m-%d'),
                'get_current_time': lambda: datetime.now().strftime('%H:%M:%S'),
            }
            logger.info("Calendar module loaded")
        except Exception as e:
            logger.warning(f"Failed to load calendar module: {e}")
            
        # System module
        try:
            import psutil
            self.modules['system'] = {
                'name': 'System Module',
                'get_cpu_usage': lambda: psutil.cpu_percent(),
                'get_memory_usage': lambda: psutil.virtual_memory().percent,
            }
            logger.info("System module loaded")
        except ImportError:
            logger.warning("psutil not available for system module")
            
    def get_module_data(self, module_name: str) -> Optional[Dict]:
        """Get module data"""
        return self.modules.get(module_name)

# ============================================================================
# Main Kernel
# ============================================================================

class EV3Kernel:
    """Main E.V3 Kernel"""
    
    def __init__(self):
        self.llm_engine = LLMEngine()
        self.modules = ModuleSystem()
        self.ipc_server = IPCServer()
        self.running = False
        
    def start(self):
        """Start kernel"""
        self.running = True
        logger.info("="*60)
        logger.info("E.V3 Kernel v2.0.0 (Python Production Build)")
        logger.info("="*60)
        logger.info(f"LLM Model: {self.llm_engine.model_name or 'Not loaded'}")
        logger.info(f"Modules: {list(self.modules.modules.keys())}")
        logger.info("="*60)
        
        # Start IPC server in thread
        ipc_thread = threading.Thread(target=self.ipc_server.start, daemon=True)
        ipc_thread.start()
        
        # Keep kernel alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            self.stop()
            
    def stop(self):
        """Stop kernel"""
        self.running = False
        self.ipc_server.running = False
        logger.info("Kernel stopped")

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    # Create global kernel instance
    kernel = EV3Kernel()
    
    try:
        kernel.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
