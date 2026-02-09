#!/usr/bin/env python3
"""
E.V3 System Verification Script
Validates all components are present and functional
"""

import sys
import subprocess
from pathlib import Path
import json

def check(description: str, condition: bool, details: str = "") -> bool:
    """Print check result"""
    status = "✓" if condition else "✗"
    print(f"{status} {description}")
    if details:
        print(f"  {details}")
    return condition

def main():
    """Run all verification checks"""
    print("="*70)
    print("E.V3 SYSTEM VERIFICATION")
    print("="*70 + "\n")
    
    all_ok = True
    base = Path(__file__).parent
    
    # 1. Python version
    print("1. Python Environment")
    print("-" * 70)
    all_ok &= check(
        "Python version 3.10+",
        sys.version_info >= (3, 10),
        f"Current: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    
    # 2. Required files
    print("\n2. Required Files")
    print("-" * 70)
    
    required_files = [
        ("Kernel executable", base / "kernel_cpp/build/Release/EV3Kernel.exe"),
        ("Shell executable", base / "dist/Shell/Shell.exe"),
        ("Main UI", base / "main_ui.py"),
        ("Test script", base / "test_kernel.py"),
        ("Launcher batch", base / "start_ev3.bat"),
    ]
    
    for name, path in required_files:
        all_ok &= check(
            f"{name}",
            path.exists(),
            f"Path: {path}"
        )
    
    # 3. Python packages
    print("\n3. Python Dependencies")
    print("-" * 70)
    
    packages = [
        ("pywin32", "Windows Named Pipes"),
        ("pyyaml", "YAML configuration"),
        ("loguru", "Logging"),
    ]
    
    for package, purpose in packages:
        try:
            __import__(package)
            all_ok &= check(f"{package}", True, f"Purpose: {purpose}")
        except ImportError:
            all_ok &= check(f"{package}", False, f"Purpose: {purpose} [INSTALL: pip install {package}]")
    
    # 4. Optional packages
    print("\n4. Optional Packages (for real LLM)")
    print("-" * 70)
    
    optional = ["llama_cpp", "psutil"]
    for package in optional:
        try:
            __import__(package)
            print(f"✓ {package} (available)")
        except ImportError:
            print(f"○ {package} (optional, for: pip install {package.replace('_', '-')}-python)")
    
    # 5. Directory structure
    print("\n5. Directory Structure")
    print("-" * 70)
    
    dirs = [
        ("Logs directory", base / "logs"),
        ("Config directory", base / "config"),
        ("Models directory", base / "models"),
    ]
    
    for name, path in dirs:
        exists = path.exists()
        if not exists:
            path.mkdir(parents=True, exist_ok=True)
        all_ok &= check(f"{name}", True, f"Path: {path}")
    
    # 6. Configuration files
    print("\n6. Configuration Files")
    print("-" * 70)
    
    config_files = [
        ("Main config", base / "config/config.yaml"),
        ("Permissions config", base / "config/permissions.yaml"),
    ]
    
    for name, path in config_files:
        all_ok &= check(f"{name}", path.exists(), f"Path: {path}")
    
    # 7. Quick kernel test
    print("\n7. Kernel Connectivity Test")
    print("-" * 70)
    
    try:
        import win32file
        import pywintypes
        
        pipe_name = r'\\.\pipe\E.V3.v2'
        try:
            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None, win32file.OPEN_EXISTING, 0, None
            )
            
            # Test ping
            message = json.dumps({'command': 'ping'})
            win32file.WriteFile(handle, message.encode('utf-8'))
            hr, data = win32file.ReadFile(handle, 1024)
            response = json.loads(data.decode('utf-8'))
            
            all_ok &= check("Kernel accessible via IPC", response.get('response') == 'pong')
            win32file.CloseHandle(handle)
            
        except pywintypes.error:
            print("○ Kernel not currently running (this is normal, start it with: kernel_cpp\\build\\Release\\EV3Kernel.exe)")
    except ImportError:
        print("○ pywin32 not available for live test")
    
    # Final report
    print("\n" + "="*70)
    if all_ok:
        print("✓ ALL CHECKS PASSED - System ready to launch!")
        print("="*70)
        print("\nTo start E.V3:")
        print("  Method 1: start_ev3.bat")
        print("  Method 2: kernel_cpp\\build\\Release\\EV3Kernel.exe  (then)")
        print("            dist/Shell/Shell.exe")
        print("\nTo test kernel: python test_kernel.py")
        print("="*70)
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please fix issues above")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
