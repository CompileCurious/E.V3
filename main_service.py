"""
Main entry point for E.V3 Background Service
Launches the Python kernel and Python UI shell
"""

import sys
import os
import yaml
import win32event
import win32api
import subprocess
import time
from winerror import ERROR_ALREADY_EXISTS
from loguru import logger
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def check_single_instance():
    """Ensure only one instance of the service is running"""
    mutex_name = "Global\\EV3ServiceMutex"
    mutex = win32event.CreateMutex(None, True, mutex_name)  # Changed to True to immediately acquire
    last_error = win32api.GetLastError()
    
    if last_error == ERROR_ALREADY_EXISTS:
        logger.warning("E.V3 Service is already running. Exiting.")
        return None  # Return None instead of False
    
    return mutex  # Return the mutex handle to keep it alive


def load_config(config_path: str = "config/config.yaml"):
    """Load configuration from YAML"""
    try:
        config_full_path = get_resource_path(config_path)
        with open(config_full_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_full_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def setup_logging(config):
    """Setup logging configuration"""
    log_config = config.get("logging", {})
    log_level = log_config.get("level", "INFO")
    
    # Remove default handler
    logger.remove()
    
    # Add console handler only if stderr is available
    if sys.stderr is not None:
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


def main():
    """Main entry point - launches Python kernel"""
    logger.info("Starting E.V3 Privacy-Focused Desktop Companion")
    logger.info("Using Python kernel for LLM inference")
    
    # Check for single instance and keep mutex handle
    mutex = check_single_instance()
    if mutex is None:
        print("E.V3 Service is already running.")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    # Launch Python kernel as subprocess
    logger.info("Launching Python kernel...")
    kernel_script = get_resource_path("kernel_cpp/bin/EV3Kernel.py")
    
    try:
        kernel_process = subprocess.Popen(
            [sys.executable, kernel_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        logger.info("Python kernel started successfully")
        logger.info("IPC server running at: \\.\pipe\E.V3.v2")
        logger.info("Waiting for shell connection...")
        
        # Monitor kernel process
        while True:
            if kernel_process.poll() is not None:
                logger.error("Kernel process terminated unexpectedly")
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Kernel error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down E.V3 Service...")
        if kernel_process.poll() is None:
            kernel_process.terminate()
            try:
                kernel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                kernel_process.kill()
        logger.info("E.V3 Service stopped")


if __name__ == "__main__":
    main()

