"""
Main entry point for E.V3 Background Service
"""

import sys
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS
from loguru import logger

from service.core import EV3Service


def check_single_instance():
    """Ensure only one instance of the service is running"""
    mutex_name = "Global\\EV3ServiceMutex"
    mutex = win32event.CreateMutex(None, False, mutex_name)
    last_error = win32api.GetLastError()
    
    if last_error == ERROR_ALREADY_EXISTS:
        logger.warning("E.V3 Service is already running. Exiting.")
        return False
    
    return True


if __name__ == "__main__":
    # Check for single instance
    if not check_single_instance():
        print("E.V3 Service is already running.")
        sys.exit(1)
    
    service = EV3Service()
    service.initialize()
    service.start()

