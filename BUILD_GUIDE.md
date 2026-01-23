# Water Balance Application - Build Guide

Complete guide for building and distributing the Water Balance Application.

## Prerequisites

### Software Requirements
1. **Python 3.8+** (with virtual environment)
2. **PyInstaller** (installed in .venv)
3. **Inno Setup 6.x** (for Windows installer)
   - Download from: https://jrsoftware.org/isinfo.php
   - Install to default location

### Verify Installation
```powershell
# Check Python
.venv\Scripts\python --version

# Check PyInstaller
.venv\Scripts\pyinstaller --version

# Check Inno Setup (should be in PATH or Program Files)
iscc /?
```

## Build Process

### Step 1: Clean Previous Builds
```powershell
# Remove old build artifacts
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "installer_output" -Recurse -Force -ErrorAction SilentlyContinue
```

### Step 2: Build Executable with PyInstaller
```powershell
# Run the build script
.\build.ps1
```

Or manually:
```powershell
# Build using spec file
.venv\Scripts\pyinstaller water_balance.spec --clean --noconfirm
```

**Output:**
- Executable: `dist\WaterBalance\WaterBalance.exe`
- Supporting files: `dist\WaterBalance\*`

### Step 3: Test the Executable
```powershell
# Run the built executable
.\dist\WaterBalance\WaterBalance.exe
```

**Verify:**
- ✅ Application launches without errors
- ✅ UI renders correctly
- ✅ Database initializes
- ✅ License check works
- ✅ All features functional

### Step 4: Create Installer with Inno Setup

#### Option A: Using Inno Setup GUI
1. Open Inno Setup Compiler
2. File → Open → Select `installer.iss`
3. Build → Compile
4. Wait for compilation to complete

#### Option B: Using Command Line
```powershell
# Compile installer
iscc installer.iss
```

**Output:**
- Installer: `installer_output\WaterBalanceSetup_v1.0.0.exe`

### Step 5: Test the Installer
```powershell
# Run the installer
.\installer_output\WaterBalanceSetup_v1.0.0.exe
```

**Verify:**
- ✅ Installer launches and displays correctly
- ✅ Installation completes successfully
- ✅ Desktop/Start Menu shortcuts created
- ✅ Application runs from installed location
- ✅ Uninstaller works correctly

## Build Configuration Files

### water_balance.spec (PyInstaller)

**Key Settings:**
- **Entry Point:** `src/main.py`
- **Icon:** `logo/Water Balance.ico`
- **Console:** `False` (GUI application, no console window)
- **UPX:** `True` (compression enabled)
- **Name:** `WaterBalance`

**Included Data Files:**
- `config/*.yaml` → Configuration files
- `data/*.json` → Data files
- `data/diagrams/*.json` → Flow diagrams
- `logo/*.ico`, `logo/*.png` → Branding assets
- `README.md`, `LICENSE.txt` → Documentation

**Excluded:**
- Test files (`pytest`, `unittest`, `test`, `_pytest`)
- Development tools (`setuptools`, `pip`, `wheel`)

### installer.iss (Inno Setup)

**Key Settings:**
- **App Name:** Water Balance Application
- **Version:** 1.0.0
- **Publisher:** TransAfrica Resources
- **Install Directory:** `{autopf}\WaterBalance`
- **Icon:** `logo\Water Balance.ico`
- **Architecture:** x64 only
- **Compression:** LZMA2 (solid compression)

**Created Directories (with user permissions):**
- `{app}\logs` - Application logs
- `{app}\data` - User data
- `{app}\config` - Configuration
- `{app}\reports` - Generated reports

**Desktop Icons:**
- Start Menu: Water Balance
- Desktop: Water Balance (optional, unchecked by default)
- Quick Launch: Water Balance (optional, Windows 7 and below)

## Build Checklist

### Pre-Build
- [ ] All tests pass: `.venv\Scripts\python -m pytest tests -v`
- [ ] No uncommitted changes (or commit first)
- [ ] Version number updated in `installer.iss`
- [ ] `README.md` is current
- [ ] `LICENSE.txt` is included

### Build
- [ ] Clean old builds: `Remove-Item build, dist, installer_output -Recurse -Force`
- [ ] Run PyInstaller: `.\build.ps1`
- [ ] Test executable: `.\dist\WaterBalance\WaterBalance.exe`
- [ ] No errors in logs

### Installer
- [ ] Compile installer: `iscc installer.iss`
- [ ] Test installation on clean machine
- [ ] Verify all shortcuts work
- [ ] Test uninstaller

### Post-Build
- [ ] Tag release in Git: `git tag v1.0.0`
- [ ] Create GitHub release
- [ ] Upload installer to distribution server
- [ ] Update documentation with new version

## Troubleshooting

### PyInstaller Errors

#### Missing Modules
**Error:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:** Add to `hiddenimports` in `water_balance.spec`:
```python
hiddenimports=[
    'xyz',  # Add missing module
    ...
]
```

#### Icon Not Found
**Error:** `Unable to load icon file`

**Solution:** Verify icon path exists:
```powershell
Test-Path "logo\Water Balance.ico"
```

#### File Not Found During Build
**Error:** `FileNotFoundError: No such file or directory`

**Solution:** Check `added_files` paths in `water_balance.spec`:
```python
added_files = [
    ('config/*.yaml', 'config'),  # Verify path exists
    ...
]
```

### Inno Setup Errors

#### Source File Not Found
**Error:** `Source file "dist\WaterBalance\*" does not exist`

**Solution:** Run PyInstaller build first:
```powershell
.\build.ps1
```

#### Icon File Not Found
**Error:** `SetupIconFile: Cannot open file`

**Solution:** Verify icon path in `installer.iss`:
```ini
SetupIconFile=logo\Water Balance.ico
```

#### Permission Errors
**Error:** `Access denied` or `Cannot create file`

**Solution:** Run Inno Setup Compiler as Administrator

### Runtime Errors

#### Application Won't Start
**Symptoms:** Double-click exe, nothing happens

**Debug:**
1. Run from command line to see errors:
   ```powershell
   .\dist\WaterBalance\WaterBalance.exe
   ```
2. Check for missing DLLs:
   - Install Visual C++ Redistributable
   - Check Windows Event Viewer

#### Missing Dependencies
**Symptoms:** Import errors at runtime

**Solution:** Add to `hiddenimports` in spec file and rebuild

#### Data Files Not Found
**Symptoms:** File not found errors for config/data files

**Solution:** Verify files are in `added_files` list in spec file

## Version Management

### Updating Version Numbers

Update in **three** places:

1. **installer.iss** (Line 7):
   ```ini
   AppVersion=1.1.0
   ```

2. **installer.iss** (Line 15):
   ```ini
   OutputBaseFilename=WaterBalanceSetup_v1.1.0
   ```

3. **src/main.py** (or create version.py):
   ```python
   __version__ = "1.1.0"
   ```

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

Examples:
- `1.0.0` → Initial release
- `1.0.1` → Bug fix
- `1.1.0` → New feature
- `2.0.0` → Breaking change

## Distribution

### Internal Distribution
1. Copy installer to network share
2. Send email with download link
3. Include release notes

### External Distribution
1. Upload to GitHub Releases
2. Create download page
3. Update documentation website

### Installer Naming Convention
```
WaterBalanceSetup_v{VERSION}.exe

Examples:
- WaterBalanceSetup_v1.0.0.exe
- WaterBalanceSetup_v1.1.0.exe
- WaterBalanceSetup_v2.0.0-beta.exe
```

## Automated Build Script

### build.ps1 (Enhanced)

```powershell
# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Run PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Cyan
.venv\Scripts\pyinstaller water_balance.spec --clean --noconfirm

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable: dist\WaterBalance\WaterBalance.exe" -ForegroundColor Green
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Optional: Run Inno Setup
Write-Host "Creating installer with Inno Setup..." -ForegroundColor Cyan
iscc installer.iss

if ($LASTEXITCODE -eq 0) {
    Write-Host "Installer created successfully!" -ForegroundColor Green
    Write-Host "Installer: installer_output\WaterBalanceSetup_v1.0.0.exe" -ForegroundColor Green
} else {
    Write-Host "Installer creation failed!" -ForegroundColor Red
    exit 1
}
```

## Quick Reference

### Build Commands
```powershell
# Clean build
.\build.ps1

# Manual PyInstaller
.venv\Scripts\pyinstaller water_balance.spec --clean --noconfirm

# Manual Inno Setup
iscc installer.iss
```

### Test Commands
```powershell
# Test executable
.\dist\WaterBalance\WaterBalance.exe

# Test installer
.\installer_output\WaterBalanceSetup_v1.0.0.exe
```

### Cleanup Commands
```powershell
# Remove all build artifacts
Remove-Item build, dist, installer_output -Recurse -Force -ErrorAction SilentlyContinue
```

---

**Last Updated:** January 23, 2026  
**Maintainer:** Development Team
