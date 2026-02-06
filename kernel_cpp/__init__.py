"""
E.V3 C++ Kernel Python Bridge

This module provides a Python interface to the C++ kernel, either via:
1. Direct import of the C extension module (if available)
2. Subprocess management of the kernel executable
3. IPC client connection

Usage:
    from kernel_cpp import CppKernelBridge
    
    bridge = CppKernelBridge()
    bridge.start()
    
    # The bridge handles kernel lifecycle and provides IPC access
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from loguru import logger

# Try to import the C extension
try:
    import ev3_kernel_cpp as _cpp_kernel
    HAS_CPP_EXTENSION = True
except ImportError:
    HAS_CPP_EXTENSION = False
    _cpp_kernel = None


def get_kernel_exe_path() -> Optional[Path]:
    """Find the C++ kernel executable"""
    base = Path(__file__).parent
    
    # Check common locations
    candidates = [
        base / "build" / "bin" / "EV3Kernel.exe",
        base / "build" / "Release" / "EV3Kernel.exe",
        base / "bin" / "EV3Kernel.exe",
        base.parent / "bin" / "EV3Kernel.exe",
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None


class CppKernelBridge:
    """
    Bridge between Python shell and C++ kernel.
    
    Handles kernel lifecycle and provides access to kernel features.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._use_extension = HAS_CPP_EXTENSION
        
    @property
    def is_running(self) -> bool:
        """Check if kernel is running"""
        if self._use_extension and _cpp_kernel:
            return _cpp_kernel.is_running()
        return self._running and self._process is not None and self._process.poll() is None
    
    def start(self) -> bool:
        """Start the C++ kernel"""
        if self.is_running:
            logger.warning("Kernel already running")
            return True
        
        if self._use_extension and _cpp_kernel:
            return self._start_extension()
        else:
            return self._start_subprocess()
    
    def stop(self) -> bool:
        """Stop the C++ kernel"""
        if self._use_extension and _cpp_kernel:
            return self._stop_extension()
        else:
            return self._stop_subprocess()
    
    def _start_extension(self) -> bool:
        """Start kernel via C extension"""
        try:
            _cpp_kernel.initialize(self.config_path)
            
            # Start in background thread
            def run_kernel():
                _cpp_kernel.start()
            
            thread = threading.Thread(target=run_kernel, daemon=True)
            thread.start()
            
            self._running = True
            logger.info("C++ kernel started (extension mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start C++ kernel: {e}")
            return False
    
    def _stop_extension(self) -> bool:
        """Stop kernel via C extension"""
        try:
            _cpp_kernel.stop()
            self._running = False
            logger.info("C++ kernel stopped (extension mode)")
            return True
        except Exception as e:
            logger.error(f"Failed to stop C++ kernel: {e}")
            return False
    
    def _start_subprocess(self) -> bool:
        """Start kernel as subprocess"""
        exe_path = get_kernel_exe_path()
        
        if not exe_path:
            logger.error("C++ kernel executable not found")
            return False
        
        try:
            self._process = subprocess.Popen(
                [str(exe_path), "-c", self.config_path],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self._running = True
            logger.info(f"C++ kernel started (subprocess mode): {exe_path}")
            
            # Give kernel time to initialize
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start C++ kernel subprocess: {e}")
            return False
    
    def _stop_subprocess(self) -> bool:
        """Stop kernel subprocess"""
        if not self._process:
            return True
        
        try:
            self._process.terminate()
            
            # Wait for graceful shutdown
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            
            self._process = None
            self._running = False
            logger.info("C++ kernel stopped (subprocess mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop C++ kernel: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: int = 128, 
                 temperature: float = 0.7,
                 callback: Optional[Callable[[str], bool]] = None) -> str:
        """
        Generate text using the LLM.
        
        Only available with C extension. For subprocess mode, use IPC.
        """
        if not self._use_extension or not _cpp_kernel:
            raise RuntimeError("Direct generation only available with C extension. Use IPC.")
        
        return _cpp_kernel.generate(
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature,
            callback=callback
        )
    
    def switch_mode(self, mode: str) -> bool:
        """
        Switch LLM mode ('fast' or 'deep').
        
        Only available with C extension. For subprocess mode, use IPC.
        """
        if not self._use_extension or not _cpp_kernel:
            raise RuntimeError("Mode switching only available with C extension. Use IPC.")
        
        return _cpp_kernel.switch_mode(mode)
    
    def get_mode(self) -> str:
        """
        Get current LLM mode.
        
        Only available with C extension. For subprocess mode, use IPC.
        """
        if not self._use_extension or not _cpp_kernel:
            raise RuntimeError("Mode query only available with C extension. Use IPC.")
        
        return _cpp_kernel.get_mode()


def check_cpp_kernel_available() -> Dict[str, Any]:
    """
    Check if C++ kernel is available and return status info.
    
    Returns:
        Dict with:
        - available: bool - Whether C++ kernel can be used
        - extension: bool - Whether C extension is available
        - executable: Optional[str] - Path to executable if found
        - reason: str - Explanation of availability status
    """
    result = {
        "available": False,
        "extension": HAS_CPP_EXTENSION,
        "executable": None,
        "reason": ""
    }
    
    if HAS_CPP_EXTENSION:
        result["available"] = True
        result["reason"] = "C extension module available"
        return result
    
    exe_path = get_kernel_exe_path()
    if exe_path:
        result["available"] = True
        result["executable"] = str(exe_path)
        result["reason"] = f"Executable found at {exe_path}"
        return result
    
    result["reason"] = "No C++ kernel available. Build with CMake or fall back to Python kernel."
    return result


# Convenience function for checking availability
def is_available() -> bool:
    """Quick check if C++ kernel is available"""
    return check_cpp_kernel_available()["available"]
