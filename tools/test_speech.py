"""
Test script for E.V3 speech system
Demonstrates sending speak commands from kernel to shell
"""

import json
import time
from pathlib import Path
from ipc import IPCClient


def test_speech_commands():
    """Test various speech commands"""
    
    print("E.V3 Speech System Test")
    print("=" * 50)
    print()
    
    # Connect to shell IPC
    client = IPCClient(pipe_name=r"\\.\pipe\E.V3.v2")
    
    print("Connecting to E.V3 Shell...")
    if not client.connect(timeout_ms=5000):
        print("❌ Failed to connect to shell. Is it running?")
        print("   Start with: python main_ui.py")
        return
    
    print("✅ Connected!")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Basic greeting",
            "text": "Hello! How are you today?",
            "emotion": "happy"
        },
        {
            "name": "Calm response",
            "text": "I am functioning optimally, thank you for asking.",
            "emotion": "calm"
        },
        {
            "name": "Excited response",
            "text": "That's amazing! Let me help you with that right away!",
            "emotion": "excited"
        },
        {
            "name": "Sad response",
            "text": "I'm sorry to hear that. Is there anything I can do to help?",
            "emotion": "sad"
        },
        {
            "name": "Neutral statement",
            "text": "The current system status is normal. All services are operational.",
            "emotion": "neutral"
        },
        {
            "name": "Long text",
            "text": "Good afternoon. I've been monitoring your system, and everything appears to be running smoothly. There are no security alerts at this time.",
            "emotion": "calm"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"  Text: {test['text']}")
        print(f"  Emotion: {test['emotion']}")
        
        # Send speak command
        message = {
            "type": "speak",
            "text": test['text'],
            "emotion": test['emotion'],
            "blocking": False
        }
        
        try:
            client.send_message("speak", {
                "text": test['text'],
                "emotion": test['emotion'],
                "blocking": False
            })
            print("  ✅ Sent")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
        time.sleep(3)  # Wait between tests
    
    print("=" * 50)
    print("Tests complete!")
    print()
    print("Check shell logs for speech generation details.")
    

def list_voicepacks():
    """List available voicepacks"""
    speech_dir = Path("models/speech")
    
    if not speech_dir.exists():
        print("No speech directory found")
        return
    
    print("Available Voicepacks:")
    print("=" * 50)
    
    for folder in speech_dir.iterdir():
        if not folder.is_dir():
            continue
        
        config_file = folder / "config.json"
        if not config_file.exists():
            continue
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"📦 {folder.name}")
            print(f"   Name: {config.get('name', 'Unknown')}")
            print(f"   Version: {config.get('version', 'Unknown')}")
            print(f"   Type: {config.get('type', 'Unknown')}")
            print(f"   Author: {config.get('author', 'Unknown')}")
            print()
            
        except Exception as e:
            print(f"❌ {folder.name}: Error loading config - {e}")
            print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_voicepacks()
    else:
        print("Make sure the E.V3 Shell is running before running this test!")
        print("Start with: python main_ui.py")
        print()
        
        input("Press Enter to continue...")
        test_speech_commands()
