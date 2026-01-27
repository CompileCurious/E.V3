# E.V3 Development Notes

## Development Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional)
pip install pytest black pylint mypy
```

## Code Style

- **Formatter**: Black (line length: 100)
- **Linter**: Pylint
- **Type Checking**: MyPy (optional)
- **Docstrings**: Google style

## Project Conventions

### File Organization
- One class per file (generally)
- `__init__.py` exports public API
- Keep modules focused and cohesive

### Naming
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Imports
```python
# Standard library
import sys
import os

# Third-party
from PySide6.QtWidgets import QMainWindow
import numpy as np

# Local
from service.state import CompanionStateMachine
```

## Testing

### Run Tests
```bash
python tests/test_components.py
```

### Add New Tests
```python
def test_new_feature():
    """Test description"""
    # Arrange
    # Act
    # Assert
    pass
```

## Debugging

### Enable Debug Logging
Edit `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

### Check Logs
- Service: `logs/ev3.log`
- UI: `logs/ev3_ui.log`

### Debug Mode
```bash
# Run with Python debugger
python -m pdb main_service.py

# Or use IDE debugger (VS Code, PyCharm)
```

## Common Development Tasks

### Add New Event Type
1. Create listener in `service/events/`
2. Register in `EventManager`
3. Add callback in `EV3Service`
4. Handle in state machine

### Add New Animation
1. Add method in `AnimationController`
2. Call from state transition
3. Test with different states

### Modify UI Layout
1. Edit `CompanionWindow`
2. Update stylesheets
3. Test window positioning

### Change State Machine
1. Edit `state_machine.py`
2. Add new states/transitions
3. Update handlers in service

## Performance Profiling

### CPU Profiling
```python
import cProfile
cProfile.run('main()', 'profile.stats')

# Analyze
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(10)
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def function_to_profile():
    pass
```

## Building Distribution

### Create Executable (PyInstaller)
```bash
pip install pyinstaller

# Service
pyinstaller --onefile --noconsole main_service.py

# UI
pyinstaller --onefile --windowed main_ui.py
```

### Create Installer (NSIS)
```bash
# Create installer script
makensis installer.nsi
```

## Security Considerations

### Code Review Checklist
- [ ] No hardcoded credentials
- [ ] All user input validated
- [ ] External data sanitized
- [ ] Privacy controls respected
- [ ] Logs don't contain PII
- [ ] API keys from environment
- [ ] File permissions correct

### Vulnerability Scanning
```bash
# Check dependencies
pip install safety
safety check

# Check code
pip install bandit
bandit -r service/ ui/
```

## Contributing Guidelines

1. **Fork** the repository
2. **Create** feature branch
3. **Make** changes with tests
4. **Commit** with clear messages
5. **Push** to branch
6. **Create** pull request

### Commit Messages
```
type(scope): subject

body

footer
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(animation): add custom gesture support

- Add gesture playback system
- Support for custom animation files
- Update documentation

Closes #123
```

## Known Issues

### Issue Template
```markdown
**Description**
Brief description of the issue

**Steps to Reproduce**
1. Step 1
2. Step 2
3. ...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Windows 10/11
- Python: 3.10
- GPU: NVIDIA/AMD/Intel

**Logs**
Relevant log excerpts
```

## Release Process

1. Update version in `__init__.py`
2. Update `CHANGELOG.md`
3. Run all tests
4. Build distribution
5. Tag release
6. Create release notes

## Useful Resources

### Python Libraries
- PySide6: https://doc.qt.io/qtforpython/
- PyOpenGL: http://pyopengl.sourceforge.net/
- llama-cpp-python: https://github.com/abetlen/llama-cpp-python

### 3D Formats
- GLTF: https://www.khronos.org/gltf/
- VRM: https://vrm.dev/

### Windows API
- pywin32: https://github.com/mhammond/pywin32
- WMI: https://pypi.org/project/WMI/

## Architecture Decisions

### Why Named Pipes?
- Native Windows IPC
- Fast and secure
- Local-only communication
- No network overhead

### Why Local LLM?
- Privacy preservation
- No API costs
- No rate limits
- Offline capable

### Why OpenGL over DirectX?
- Cross-platform potential
- Mature Python bindings
- Simpler shader system
- Wide GPU support

### Why PySide6 over Tkinter?
- Modern UI capabilities
- Better transparency support
- OpenGL integration
- Professional appearance

## Future Architecture

### Potential Improvements
1. **Plugin System**: Modular extensions
2. **Config GUI**: Visual configuration editor
3. **Model Marketplace**: Share character models
4. **Voice Integration**: Speech input/output
5. **Multi-platform**: Linux/macOS support

### Scalability Considerations
- Event queue optimization
- LLM inference caching
- Animation interpolation
- Resource pooling
