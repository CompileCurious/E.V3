"""Create distribution package folder and copy built executables, config and docs.
Run this after building Kernel.exe and Shell.exe into ./dist.
"""
import shutil
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
dist = root / 'dist' / 'EV3_Package'

print(f"Creating distribution package at: {dist}")
dist.mkdir(parents=True, exist_ok=True)

# Copy executables if present
def _copy_exe(name):
    # Prefer onedir output folder, fall back to single-file exe
    dir_path = root / 'dist' / name
    exe_path = root / 'dist' / f"{name}.exe"
    if dir_path.exists() and (dir_path / f"{name}.exe").exists():
        shutil.copy(dir_path / f"{name}.exe", dist / f"{name}.exe")
        print(f"Copied {name}.exe from onedir output")
    elif exe_path.exists():
        shutil.copy(exe_path, dist / f"{name}.exe")
        print(f"Copied {name}.exe")
    else:
        print(f"Warning: {name}.exe not found in dist/")

for name in ('Kernel', 'Shell'):
    _copy_exe(name)

# Copy config
cfg_src = root / 'config'
if cfg_src.exists():
    shutil.copytree(cfg_src, dist / 'config', dirs_exist_ok=True)
    print("Copied config/")

# Create models folders
src_models = root / 'models'
dst_models = dist / 'models'
if src_models.exists():
    # Copy entire models tree (character, llm, speech, and docs)
    shutil.copytree(src_models, dst_models, dirs_exist_ok=True)
    print("Copied models/ (including character and llm)")
else:
    (dist / 'models' / 'llm').mkdir(parents=True, exist_ok=True)
    (dist / 'models' / 'character').mkdir(parents=True, exist_ok=True)
    print("Created empty models/ folders")

# Copy documentation
for doc in ('README.md', 'CHANGELOG.md'):
    s = root / doc
    if s.exists():
        shutil.copy(s, dist / doc)

# Copy .env.example
env = root / '.env.example'
if env.exists():
    shutil.copy(env, dist / '.env.example')

# Create logs dir
(dist / 'logs').mkdir(exist_ok=True)

# Create Start_EV3.bat launcher
launcher = dist / 'Start_EV3.bat'
launcher.write_text(r"""@echo off
title E.V3 Companion
echo ================================================
echo E.V3 Privacy-Focused Desktop Companion
echo ================================================
echo.
echo Starting kernel...
start "E.V3 Kernel" /MIN Kernel.exe
timeout /t 2 /nobreak >NUL
echo Starting shell...
start "E.V3 Shell" Shell.exe
echo.
echo ================================================
echo E.V3 is now running!
echo ================================================
echo.
pause
""")
print("Created Start_EV3.bat")

print("Distribution package is ready:")
print(dist)
