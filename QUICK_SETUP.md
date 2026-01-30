# E.V3 Quick Setup Reference

## Fresh Clone Setup

```bash
# 1. Clone repo (code only, ~5MB)
git clone https://github.com/yourusername/E.V3.git
cd E.V3

# 2. Setup environment (CHOOSE ONE)

# Option A: Automated (recommended)
setup.bat

# Option B: Manual
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install llama-cpp-python

# 3. Download models
python tools/download_phi3.py
# Add your character model to models/character/

# 4. Run
start_ev3.bat  # or start_with_313.bat for Python 3.13 portable
```

## What's in the Repo

✅ **Included** (tracked by git):
- Source code (`.py` files)
- Documentation (`.md` files)  
- Config templates (`config/config.yaml`)
- Setup scripts (`setup.bat`, `requirements.txt`)
- Directory structure

❌ **NOT Included** (you set up locally):
- Python environments (`.venv/`, etc.)
- Python packages/wheels (`*.whl`)
- Build artifacts (`build/`, `dist/`, `*.exe`)
- Log files (`logs/`)
- Downloaded models (`models/llm/*.gguf`, `models/character/*.vrm`)

## Dependencies

### Install via requirements.txt:
```bash
pip install -r requirements.txt
```

Installs:
- PySide6 (GUI)
- PyOpenGL (3D rendering)
- pygltflib (model loading)
- loguru (logging)
- pyyaml (config)
- pywin32 (Windows integration)
- pynput (hotkeys)
- Pillow (textures)

### Install separately:
```bash
pip install llama-cpp-python  # Required for LLM
```

## File Structure

```
E.V3/
├── kernel/          # Microkernel source
├── modules/         # Capability modules
├── service/         # Service implementations
├── ui/              # 3D UI source
├── ipc/             # IPC implementation
├── config/          # Configuration files
├── models/          # Empty (download models)
│   ├── llm/         # LLM models (.gguf)
│   ├── character/   # 3D models (.vrm)
│   └── speech/      # TTS models
├── logs/            # Empty (generated at runtime)
├── .venv/           # Your environment (NOT in git)
└── requirements.txt # Dependency list
```

## Common Commands

```bash
# Activate environment
.venv\Scripts\activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Run E.V3
start_ev3.bat

# Run with Python 3.13 portable
start_with_313.bat

# Build executable
build.bat

# Check environment
python -c "import llama_cpp; print('OK')"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'llama_cpp'" | `pip install llama-cpp-python` |
| "No module named 'PySide6'" | `pip install -r requirements.txt` |
| LLM not working | Install llama-cpp-python, download model |
| Model not found | Check `models/llm/` for .gguf files |
| Import errors | Activate venv: `.venv\Scripts\activate` |

## Documentation

- [README.md](README.md) - Main documentation
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - Detailed setup guide
- [REPO_CLEANUP.md](REPO_CLEANUP.md) - What changed
- [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md) - Complete walkthrough
- [models/MODEL_SETUP.md](models/MODEL_SETUP.md) - Model download guide

## Environment Variables (Optional)

Create `.env` file (NOT tracked):
```bash
E.V3_LLM_MODE=fast
E.V3_GPU_LAYERS=35
OPENAI_API_KEY=your_key  # Only for external LLM
```

---

**Tip**: The repo is now clean and lean. Set up your environment once, and you're good to go!
