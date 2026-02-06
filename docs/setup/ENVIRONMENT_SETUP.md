# E.V3 Environment Setup Guide

This guide explains how to set up a clean Python environment for E.V3 development/usage.

## Overview

E.V3 does **NOT** include Python environments or binary dependencies in the repository. This keeps the repo clean and ensures you have control over your local setup.

## What's NOT in the Repository

The following are **excluded from git** (local only):
- Python virtual environments (`.venv/`, `venv/`, etc.)
- Portable Python installations (`.python313_portable/`)
- Python wheel files (`*.whl`)
- Compiled binaries (`*.pyd`, `*.dll`, `*.exe`)
- Build artifacts (`build/`, `dist/`)
- Log files (`logs/`)
- Downloaded models (`models/llm/`, `models/character/*.vrm`)

## Setup Methods

### Method 1: Automated Setup (Recommended)

Run the included setup script:

```batch
setup.bat
```

This will:
1. Check Python version
2. Create a virtual environment in `.venv/`
3. Install all dependencies from `requirements.txt`
4. Attempt to install `llama-cpp-python`
5. Create necessary directories

### Method 2: Manual Virtual Environment

For more control over your environment:

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
.venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install core dependencies
pip install -r requirements.txt

# 5. Install llama-cpp-python separately
# Choose ONE based on your hardware:

# CPU-only (easiest, works everywhere)
pip install llama-cpp-python

# GPU with CUDA 12.1 (faster, requires NVIDIA GPU + CUDA Toolkit)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# GPU with CUDA 11.8
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118
```

### Method 3: Portable Python 3.13

If you prefer a portable Python installation:

```bash
# 1. Download Python 3.13 embeddable from python.org
# Extract to: .python313_portable/

# 2. Setup pip in portable Python
.python313_portable\python.exe get-pip.py

# 3. Install dependencies
.python313_portable\python.exe -m pip install -r requirements.txt
.python313_portable\python.exe -m pip install llama-cpp-python

# 4. Use the included launcher
start_with_313.bat
```

## Python Version Compatibility

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.13.x | ✅ Recommended | Best llama-cpp-python support |
| 3.12.x | ✅ Supported | Fully compatible |
| 3.11.x | ✅ Supported | Fully compatible |
| 3.10.x | ✅ Supported | Minimum version |
| 3.9.x | ⚠️ Limited | May work but not tested |
| 3.14.x | ⚠️ Experimental | Wheel compatibility issues |

## Dependency Details

### Core Dependencies (Always Required)

```
PySide6>=6.6.0          # Qt6 GUI framework
PyOpenGL>=3.1.7         # OpenGL 3D rendering
numpy>=1.24.0           # Array operations
loguru>=0.7.0           # Logging
pyyaml>=6.0.1           # Configuration
pywin32>=306            # Windows integration
pynput>=1.7.6           # Global hotkeys
pygltflib>=1.16.0       # Model loading
Pillow>=10.0.0          # Texture loading
```

### LLM Support (Required for AI)

```
llama-cpp-python>=0.3.0 # Local LLM inference
```

**Installation Issues?**
- Make sure you have Python 3.10-3.13
- For GPU: Install CUDA Toolkit first
- For wheels: Match Python version (cp313 = Python 3.13)

### Optional Dependencies

```
pygame>=2.5.0           # Audio playback (TTS)
onnxruntime>=1.16.0     # Neural TTS (Piper)
openai>=1.0.0           # External LLM API
```

## Verifying Your Setup

After installation, verify everything works:

```bash
# Activate your environment
.venv\Scripts\activate

# Check Python version
python --version

# Test imports
python -c "import PySide6; print('PySide6: OK')"
python -c "import OpenGL; print('PyOpenGL: OK')"
python -c "import pygltflib; print('pygltflib: OK')"
# NOTE: llama-cpp-python is no longer required - use C++ kernel instead
# python -c "import llama_cpp; print('llama-cpp-python: OK')"

# List installed packages
pip list
```

## Troubleshooting

### "No module named 'llama_cpp'"

**Note**: With the C++ kernel rewrite, `llama-cpp-python` is **no longer required**.

The C++ kernel provides:
- 2-3x faster inference than Python bindings
- Direct llama.cpp integration
- Persistent model loading
- Native async/streaming

See [kernel_cpp/docs/BUILD.md](../../kernel_cpp/docs/BUILD.md) for build instructions.

If you're using the legacy Python kernel:
```bash
pip install llama-cpp-python
```

### "llama-cpp-python wheel not compatible"

**Cause**: Python version mismatch (e.g., trying to use cp313 wheel on Python 3.14)

**Solution**: 
- Use Python 3.13 if you have a cp313 wheel
- Or install from PyPI: `pip install llama-cpp-python`
- Or switch to the C++ kernel for better performance

### "CUDA error" or GPU not detected

**Solution**:
1. Install NVIDIA CUDA Toolkit (12.1 or 11.8)
2. Reinstall llama-cpp-python with CUDA support
3. Or use CPU-only version

### PySide6 or PyOpenGL errors

**Solution**:
```bash
pip install --upgrade PySide6 PyOpenGL
```

### Import errors after git pull

**Solution**: Dependencies may have changed. Reinstall:
```bash
pip install -r requirements.txt --upgrade
```

## Keeping Your Environment Clean

### When pulling updates:

```bash
git pull
pip install -r requirements.txt --upgrade  # Update dependencies if changed
```

### When switching branches:

```bash
git checkout feature-branch
pip install -r requirements.txt  # Ensure dependencies match
```

### Cleaning up:

```bash
# Remove virtual environment
deactivate
rmdir /s .venv

# Remove caches
rmdir /s __pycache__
rmdir /s build
rmdir /s dist

# Recreate clean environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

E.V3 doesn't require environment variables for basic operation, but you can use them:

### Create `.env` file (NOT tracked in git):

```bash
# LLM Configuration
E.V3_LLM_MODE=fast                  # "fast" or "deep"
E.V3_GPU_LAYERS=35                  # GPU offloading

# External API (optional)
OPENAI_API_KEY=your_key_here        # Only if using external LLM

# Paths (optional overrides)
E.V3_MODEL_PATH=custom/path/to/models
E.V3_CONFIG_PATH=custom/config.yaml
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Best Practices

1. **Always use a virtual environment** - Keeps dependencies isolated
2. **Update requirements.txt** - If you add dependencies, update the file
3. **Don't commit environments** - They're local-only for a reason
4. **Document new dependencies** - Add comments explaining why
5. **Test on clean environment** - Periodically recreate from scratch

## Getting Help

- Check [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md) for complete setup guide
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues (if exists)
- Review logs in `logs/ev3.log` for errors
- Check GitHub Issues for known problems

---

**Remember**: Your local environment is yours alone. The repo only contains source code and documentation!
