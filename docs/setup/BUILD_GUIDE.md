# Building E.V3 Executables

This guide explains how to build standalone .exe files for E.V3.

## Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# Optional: Install UPX for smaller executables
# Download from: https://upx.github.io/
# Place upx.exe in PATH or project root
```

## Quick Build

### Option 1: Automated Build Script (Recommended)
```bash
build.bat
```

This will:
1. Install PyInstaller if needed
2. Build both service and UI executables
3. Create distribution package
4. Include all necessary files

### Option 2: Manual Build
```bash
# Build service
pyinstaller EV3Service.spec

# Build UI
pyinstaller EV3Companion.spec

# Output in dist/ folder
```

## Build Output

After building, you'll have:

```
dist/EV3_Package/
├── EV3Service.exe           # Background service
├── EV3Companion.exe         # UI application
├── Start_EV3.bat            # Quick launcher
├── Install_Service.bat      # Service installer
├── Uninstall_Service.bat    # Service uninstaller
├── START_HERE.txt           # Quick instructions
├── config/                  # Configuration files
├── models/                  # Model folders
│   ├── llm/
│   └── character/
├── logs/                    # Log folder
└── Documentation files
```

## Executable Sizes

Approximate sizes:
- **EV3Service.exe**: ~15-25 MB
- **EV3Companion.exe**: ~80-120 MB (includes Qt and OpenGL)

With UPX compression:
- **EV3Service.exe**: ~8-12 MB
- **EV3Companion.exe**: ~40-60 MB

## Distribution

### Create Distributable Package

1. **Zip the package:**
   ```bash
   # In dist/ folder
   powershell Compress-Archive -Path EV3_Package -DestinationPath EV3_v0.1.0.zip
   ```

2. **What to include:**
   - ✅ Both .exe files
   - ✅ Launcher scripts (.bat files)
   - ✅ Configuration files
   - ✅ Documentation
   - ✅ Model folder structure
   - ✅ START_HERE.txt

3. **What NOT to include:**
   - ❌ LLM models (too large, user downloads separately)
   - ❌ 3D character models (user customizes)
   - ❌ Virtual environment
   - ❌ Source code (unless open-sourcing)
   - ❌ .pyc files
   - ❌ Build folders

## Testing Executables

### Before Distribution

1. **Test on clean system:**
   - No Python installed
   - No dependencies installed
   - Fresh Windows installation

2. **Test both modes:**
   ```bash
   # Standalone mode
   Start_EV3.bat
   
   # Service mode
   Install_Service.bat  # As Administrator
   EV3Companion.exe
   ```

3. **Verify functionality:**
   - [ ] Service starts successfully
   - [ ] UI window appears
   - [ ] 3D character renders
   - [ ] IPC communication works
   - [ ] Configuration loads
   - [ ] Logs are created
   - [ ] Event monitoring works

## Troubleshooting Build Issues

### PyInstaller Not Found
```bash
pip install pyinstaller
```

### Missing Modules
Add to spec file's `hiddenimports`:
```python
hiddenimports=[
    'your.missing.module',
]
```

### DLL Errors
- Ensure all dependencies are installed
- Check that pywin32 post-install ran:
  ```bash
  python venv/Scripts/pywin32_postinstall.py -install
  ```

### Large Executable Size
1. Enable UPX compression (download UPX first)
2. Exclude unnecessary modules in spec file
3. Use `--onefile` option (already enabled)

### Runtime Errors

**"Failed to execute script"**
- Build with `console=True` temporarily to see errors
- Check hidden imports
- Verify all data files are included

**OpenGL Issues**
- User needs graphics drivers
- Test on different GPU vendors (NVIDIA, AMD, Intel)

**Missing Config**
- Verify `datas` includes config folder
- Check paths in spec file

## Advanced Customization

### Custom Icon

1. Create or download .ico file
2. Place in `assets/icon.ico`
3. Rebuild executables

### Signed Executables

```bash
# After building, sign with signtool
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com EV3Service.exe
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com EV3Companion.exe
```

### Version Information

Edit spec files to add version info:
```python
version='0.1.0',
description='E.V3 Privacy-Focused Desktop Companion',
company_name='Your Name',
```

## Creating an Installer (Optional)

### Using Inno Setup (Recommended)

1. Download Inno Setup: https://jrsoftware.org/isinfo.php

2. Create installer script (see `installer.iss`)

3. Build installer:
   ```bash
   iscc installer.iss
   ```

### Using NSIS

See `installer.nsi` for NSIS script.

## Continuous Integration

For automated builds:

```yaml
# GitHub Actions example
- name: Build executables
  run: |
    pip install pyinstaller
    python build_exe.py

- name: Upload artifacts
  uses: actions/upload-artifact@v2
  with:
    name: EV3-Windows
    path: dist/EV3_Package/
```

## Performance Optimization

### Reduce Startup Time

1. Use `--onefile` (already enabled)
2. Exclude unused modules
3. Minimize hidden imports
4. Consider `--noupx` if UPX causes slowdown

### Reduce Size

1. Enable UPX compression
2. Exclude test and dev modules
3. Strip debug symbols
4. Use `--strip` option

## Distribution Checklist

Before releasing:

- [ ] Test on clean Windows system
- [ ] Verify all features work
- [ ] Check executable sizes
- [ ] Test installation scripts
- [ ] Include clear documentation
- [ ] Test service installation/removal
- [ ] Verify no hardcoded paths
- [ ] Check log file creation
- [ ] Test with and without admin rights
- [ ] Scan with antivirus (avoid false positives)
- [ ] Create SHA256 checksums
- [ ] Write release notes

## Release Process

1. **Build executables:**
   ```bash
   build.bat
   ```

2. **Test thoroughly**

3. **Create distribution package:**
   ```bash
   cd dist
   powershell Compress-Archive -Path EV3_Package -DestinationPath EV3_v0.1.0_Windows.zip
   ```

4. **Generate checksums:**
   ```bash
   certutil -hashfile EV3_v0.1.0_Windows.zip SHA256
   ```

5. **Create release notes**

6. **Upload to distribution platform**

## Support

If users report issues:

1. Ask for `logs/ev3.log` and `logs/ev3_ui.log`
2. Check Windows version and architecture
3. Verify GPU drivers are up to date
4. Test on similar system configuration
5. Rebuild with `console=True` for debugging
