#!/usr/bin/env python3
"""Test IPC client"""
import json
import sys

try:
    import win32pipe
    import win32file
    import pywintypes
    
    pipe_name = r'\\.\pipe\E.V3.v2'
    print(f"Connecting to {pipe_name}...")
    
    try:
        handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )
        print("[OK] Connected to kernel!")
        
        # Test ping
        message = json.dumps({'command': 'ping'})
        print(f"Sending: {message}")
        win32file.WriteFile(handle, message.encode('utf-8'))
        
        # Read response
        hr, data = win32file.ReadFile(handle, 1024)
        response = data.decode('utf-8')
        print(f"Response: {response}")
        
        win32file.CloseHandle(handle)
        
    except pywintypes.error as e:
        print(f"Error: {e}")
        print("Kernel may not be running")
        sys.exit(1)
        
except ImportError:
    print("pywin32 not installed, trying socket fallback...")
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 9999))
        message = json.dumps({'command': 'ping'})
        sock.send(message.encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
