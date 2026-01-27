# E.V3 - Building and Distribution Quick Reference

## 🚀 Quick Build

```bash
# One command build
build.bat

# Output: dist/EV3_Package/
```

## 📦 What Gets Built

- **EV3Service.exe** (~15-25 MB) - Background service
- **EV3Companion.exe** (~80-120 MB) - 3D UI application
- **Launcher scripts** - Easy startup
- **Configuration** - Ready to customize
- **Documentation** - User guides

## 🎯 Build Process

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Run Build**
   ```bash
   build.bat
   ```

3. **Test**
   ```bash
   cd dist\EV3_Package
   Start_EV3.bat
   ```

4. **Distribute**
   ```bash
   # Create zip
   powershell Compress-Archive -Path EV3_Package -DestinationPath EV3_v0.1.0.zip
   ```

## 📝 Distribution Checklist

### Include:
- ✅ EV3Service.exe
- ✅ EV3Companion.exe
- ✅ Start_EV3.bat
- ✅ Install_Service.bat
- ✅ Uninstall_Service.bat
- ✅ config/ folder
- ✅ models/ folder structure
- ✅ Documentation
- ✅ START_HERE.txt

### Don't Include:
- ❌ LLM models (too large, ~4GB)
- ❌ Virtual environment
- ❌ Source .py files
- ❌ Build artifacts
- ❌ .git folder

## 🎨 Optional: Create Installer

```bash
# Install Inno Setup first
# Download from: https://jrsoftware.org/isinfo.php

# Build installer
create_installer.bat

# Output: installer/EV3_Setup_v0.1.0.exe
```

## 🧪 Testing Executables

### Before Release:
1. **Clean system test** - No Python installed
2. **Both modes** - Standalone and Service
3. **All features** - Events, LLM, Calendar, 3D
4. **Different Windows versions** - 10 and 11
5. **Different GPUs** - NVIDIA, AMD, Intel

### Quick Test:
```bash
cd dist\EV3_Package
Start_EV3.bat
# Check: Does companion appear?
# Check: Do logs get created?
# Check: Can you dismiss alerts?
```

## 📊 File Sizes

| Component | Size | Compressed |
|-----------|------|------------|
| EV3Service.exe | ~20 MB | ~10 MB |
| EV3Companion.exe | ~100 MB | ~50 MB |
| Full Package (zip) | ~130 MB | ~65 MB |
| With LLM Model | ~4.5 GB | ~4.2 GB |

## 🐛 Common Build Issues

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Hidden import missing"
Edit spec files, add to `hiddenimports`:
```python
hiddenimports=['missing.module']
```

### "DLL error"
```bash
# Reinstall pywin32
pip uninstall pywin32
pip install pywin32
python venv/Scripts/pywin32_postinstall.py -install
```

### Large executable
- Enable UPX compression (download from upx.github.io)
- Exclude unnecessary modules
- Use --onefile (already enabled)

## 🎁 Distribution Methods

### Option 1: Direct Download
1. Upload EV3_v0.1.0.zip to file host
2. Share download link
3. Users extract and run

### Option 2: Installer
1. Create with Inno Setup
2. Distribute EV3_Setup_v0.1.0.exe
3. Professional installation experience

### Option 3: GitHub Release
1. Create release on GitHub
2. Attach zip/installer
3. Write release notes
4. Tag version

## 📋 Release Checklist

Before publishing:
- [ ] Build executables successfully
- [ ] Test on clean Windows system
- [ ] Verify all features work
- [ ] Update version numbers
- [ ] Write release notes
- [ ] Create changelog entry
- [ ] Generate SHA256 checksums
- [ ] Test installer (if using)
- [ ] Update documentation
- [ ] Tag git release

## 🔐 Security

### Sign Executables (Optional)
```bash
# Get code signing certificate
# Sign with signtool
signtool sign /f cert.pfx /p password /t http://timestamp.server EV3Service.exe
signtool sign /f cert.pfx /p password /t http://timestamp.server EV3Companion.exe
```

### Checksums
```bash
# Generate SHA256
certutil -hashfile dist\EV3_Package\EV3Service.exe SHA256
certutil -hashfile dist\EV3_Package\EV3Companion.exe SHA256

# Include in release notes
```

## 💡 Tips

1. **Build on clean system** - Avoid dependency pollution
2. **Test thoroughly** - On different machines
3. **Keep it simple** - Clear documentation
4. **Version everything** - Track changes
5. **User feedback** - Listen and improve

## 🆘 Support

If users report issues:
1. Ask for logs (logs/ev3.log, logs/ev3_ui.log)
2. Check Windows version
3. Verify GPU drivers
4. Test on similar system
5. Rebuild with debug enabled

## 📚 Resources

- **PyInstaller Docs**: https://pyinstaller.org/
- **Inno Setup**: https://jrsoftware.org/isinfo.php
- **UPX Compression**: https://upx.github.io/
- **Code Signing**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool

## 🎉 Ready to Build!

```bash
# Run this now:
build.bat
```

Your E.V3 executables will be ready in `dist/EV3_Package/`!
