"""Build only the Shell executable using PyInstaller.
This helper uses a list-based subprocess call to avoid shell escaping issues on Windows.
"""
import os
import sys
import subprocess

if sys.platform == "win32":
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

print("Building Shell executable (UI) with PyInstaller...")

def _choose_icon():
    for name in ("E.V3.ico", "icon.ico"):
        path = os.path.join("assets", name)
        if os.path.exists(path):
            return f"--icon={path}"
    return ""

ui_cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--name=Shell",
    "--onedir",
    "--windowed",
]

icon_flag = _choose_icon()
if icon_flag:
    ui_cmd.append(icon_flag)

# Include config and models folders
ui_cmd.append("--add-data=config;config")
ui_cmd.append("--add-data=models;models")

hidden_imports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "ui.window.shell_window",
    "OpenGL",
    "OpenGL.GL",
    "OpenGL.GLU",
]

for mod in hidden_imports:
    ui_cmd.append(f"--hidden-import={mod}")

ui_cmd.append("main_ui.py")

print("Command:", ui_cmd)

try:
    subprocess.check_call(ui_cmd)
    print("Shell executable built successfully.")
except subprocess.CalledProcessError as e:
    print("Failed to build Shell executable:", e)
    sys.exit(1)
