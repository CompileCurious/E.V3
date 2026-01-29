"""
Main entry point for E.V3 Background Service
Microkernel architecture with modular capabilities
"""

import sys
import yaml
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS
from loguru import logger
from pathlib import Path

from kernel import Kernel
from modules import StateModule, EventModule, LLMModule, CalendarModule, IPCModule


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
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
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
    """Main entry point - microkernel initialization"""
    logger.info("Starting E.V3 Privacy-Focused Desktop Companion (Microkernel Architecture)")
    
    # Check for single instance and keep mutex handle
    mutex = check_single_instance()
    if mutex is None:
        print("E.V3 Service is already running.")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    # Create kernel
    kernel = Kernel(config)
    kernel_api = kernel.get_kernel_api()
    
    # Register capability modules
    logger.info("Registering capability modules...")
    
    state_module = StateModule(kernel_api)
    kernel.register_module(state_module)
    
    event_module = EventModule(kernel_api)
    kernel.register_module(event_module)
    
    llm_module = LLMModule(kernel_api)
    kernel.register_module(llm_module)
    
    calendar_module = CalendarModule(kernel_api)
    kernel.register_module(calendar_module)
    
    ipc_module = IPCModule(kernel_api)
    kernel.register_module(ipc_module)
    
    # Load modules with their configurations
    logger.info("Loading modules...")
    module_configs = {
        "state": config.get("state_machine", {}),
        "events": config,
        "llm": config,
        "calendar": config,
        "ipc": config,
    }
    
    if not kernel.load_modules(module_configs):
        logger.error("Failed to load all modules")
        sys.exit(1)
    
    # Enable modules
    logger.info("Enabling modules...")
    if not kernel.enable_modules():
        logger.error("Failed to enable all modules")
        sys.exit(1)
    
    # Start kernel event loop
    logger.info("E.V3 Service started successfully")
    kernel.start()


if __name__ == "__main__":
    main()

