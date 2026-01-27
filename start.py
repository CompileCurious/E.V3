#!/usr/bin/env python3
"""
Quick start script for E.V3
Starts both service and UI
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    print("=" * 50)
    print("E.V3 Privacy-Focused Desktop Companion")
    print("Quick Start")
    print("=" * 50)
    print()
    
    # Check if we're in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not running in virtual environment")
        print("It's recommended to run: setup.bat first")
        print()
    
    # Start service
    print("[1/2] Starting background service...")
    service_process = subprocess.Popen(
        [sys.executable, "main_service.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    # Wait a bit for service to start
    time.sleep(2)
    
    # Start UI
    print("[2/2] Starting UI...")
    ui_process = subprocess.Popen(
        [sys.executable, "main_ui.py"]
    )
    
    print()
    print("=" * 50)
    print("E.V3 is now running!")
    print("=" * 50)
    print()
    print("Service PID:", service_process.pid)
    print("UI PID:", ui_process.pid)
    print()
    print("Press Ctrl+C to stop both processes")
    print()
    
    try:
        # Wait for UI to exit
        ui_process.wait()
    except KeyboardInterrupt:
        print("\nStopping E.V3...")
    finally:
        # Terminate both processes
        ui_process.terminate()
        service_process.terminate()
        
        print("E.V3 stopped.")


if __name__ == "__main__":
    main()
