"""
Test script for E.V3 components
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from service.state import CompanionStateMachine
        print("✓ State machine")
        
        from service.events import EventManager
        print("✓ Event manager")
        
        from service.llm import LLMManager
        print("✓ LLM manager")
        
        from service.calendar import CalendarManager
        print("✓ Calendar manager")
        
        from ipc import IPCServer, IPCClient
        print("✓ IPC")
        
        from ui.renderer import OpenGLRenderer
        print("✓ OpenGL renderer")
        
        from ui.animations import AnimationController
        print("✓ Animation controller")
        
        from ui.window import ShellWindow
        print("✓ Companion window")
        
        print("\n✓ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        import yaml
        with open("config/config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✓ Config loaded: {len(config)} sections")
        
        # Check required sections
        required = ["privacy", "service", "llm", "ui", "ipc"]
        for section in required:
            if section in config:
                print(f"  ✓ {section}")
            else:
                print(f"  ✗ {section} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_state_machine():
    """Test state machine"""
    print("\nTesting state machine...")
    
    try:
        from service.state import CompanionStateMachine, CompanionState
        
        config = {}
        sm = CompanionStateMachine(config)
        
        print(f"  Initial state: {sm.state}")
        
        # Test transitions
        sm.start_scan()
        assert sm.state == CompanionState.SCANNING.value
        print("  ✓ Transition to scanning")
        
        sm.finish_scan()
        assert sm.state == CompanionState.IDLE.value
        print("  ✓ Transition to idle")
        
        sm.trigger_alert()
        assert sm.state == CompanionState.ALERT.value
        print("  ✓ Transition to alert")
        
        print("✓ State machine working")
        return True
        
    except Exception as e:
        print(f"✗ State machine test failed: {e}")
        return False


def test_model_loader():
    """Test 3D model loader"""
    print("\nTesting 3D model loader...")
    
    try:
        from ui.renderer import ModelLoader
        
        # Create simple test model
        model = ModelLoader.create_simple_character()
        
        print(f"  Meshes: {len(model.meshes)}")
        print(f"  Bones: {len(model.bones)}")
        print(f"  Blendshapes: {len(model.blendshapes)}")
        
        print("✓ Model loader working")
        return True
        
    except Exception as e:
        print(f"✗ Model loader test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("E.V3 Component Tests")
    print("=" * 50)
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("State Machine", test_state_machine()))
    results.append(("Model Loader", test_model_loader()))
    
    print()
    print("=" * 50)
    print("Test Results")
    print("=" * 50)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
