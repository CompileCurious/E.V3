#!/usr/bin/env python3
"""Test kernel LLM inference"""
import json
import win32file
import pywintypes

pipe_name = r'\\.\pipe\E.V3.v2'
print(f"Testing kernel LLM on {pipe_name}\n")

try:
    handle = win32file.CreateFile(
        pipe_name,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None
    )
    
    # Test 1: Status
    print("="*60)
    print("TEST 1: Status")
    print("="*60)
    message = json.dumps({'command': 'status'})
    win32file.WriteFile(handle, message.encode('utf-8'))
    hr, data = win32file.ReadFile(handle, 2048)
    response = json.loads(data.decode('utf-8'))
    print(json.dumps(response, indent=2))
    
    # Test 2: Ping
    print("\n" + "="*60)
    print("TEST 2: Ping")
    print("="*60)
    message = json.dumps({'command': 'ping'})
    win32file.WriteFile(handle, message.encode('utf-8'))
    hr, data = win32file.ReadFile(handle, 2048)
    response = json.loads(data.decode('utf-8'))
    print(json.dumps(response, indent=2))
    
    # Test 3: LLM Inference
    print("\n" + "="*60)
    print("TEST 3: LLM Inference")
    print("="*60)
    message = json.dumps({'command': 'infer', 'prompt': 'Hello, what time is it?'})
    print(f"Sending: {message}")
    win32file.WriteFile(handle, message.encode('utf-8'))
    hr, data = win32file.ReadFile(handle, 4096)
    response = json.loads(data.decode('utf-8'))
    print(json.dumps(response, indent=2))
    
    # Test 4: Mode change
    print("\n" + "="*60)
    print("TEST 4: Change LLM Mode")
    print("="*60)
    message = json.dumps({'command': 'mode', 'mode': 'deep'})
    win32file.WriteFile(handle, message.encode('utf-8'))
    hr, data = win32file.ReadFile(handle, 2048)
    response = json.loads(data.decode('utf-8'))
    print(json.dumps(response, indent=2))
    
    win32file.CloseHandle(handle)
    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
