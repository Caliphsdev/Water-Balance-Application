# Build Instructions
## Water Balance Application

---

## Prerequisites

### Required Software
1. **Python 3.14+** - Installed in virtual environment (.venv)
2. **PyInstaller** - For creating executable
3. **Inno Setup 6+** - For creating Windows installer

### Installation
```powershell
# Install PyInstaller
.venv\Scripts\python.exe -m pip install pyinstaller

# Download Inno Setup from: https://jrsoftware.org/isdl.php
```

---

## Build Process

### Step 1: Prepare Application Icon

1. **Create or obtain** 256x256 PNG icon
2. **Convert to ICO** format using online tool or:
   ```powershell
   # Using ImageMagick
   magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 app_icon.ico
   ```
3. **Place icon**:
   - Copy to `assets/icons/app_icon.ico`
   - Copy to `assets/icons/installer_icon.ico`

### Step 2: Create Version Info File

Create `version_info.txt` in project root:
```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'TransAfrica Resources'),
        StringStruct(u'FileDescription', u'Water Balance Application'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'WaterBalance'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2026'),
        StringStruct(u'OriginalFilename', u'WaterBalance.exe'),
        StringStruct(u'ProductName', u'Water Balance Application'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

### Step 3: Build with PyInstaller

```powershell
# Clean previous builds
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Build executable
.venv\Scripts\python.exe -m PyInstaller water_balance.spec

# Output will be in: dist/WaterBalance/
```

### Step 4: Test Standalone Executable

```powershell
# Navigate to build output
cd dist\WaterBalance

# Run executable
.\WaterBalance.exe

# Test all features:
# - License activation
# - Data loading
# - Calculations
# - Reports generation
# - Flow diagrams
```

### Step 5: Create Installer

```powershell
# Compile Inno Setup script
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# Output will be in: installer_output/WaterBalanceSetup_v1.0.0.exe
```

### Step 6: Test Installer

1. **Run installer** on clean test machine
2. **Complete installation** wizard
3. **Launch application** from Start Menu
4. **Verify all features** work correctly
5. **Test uninstallation**

---

## Build Script (Automated)

Create `build.ps1`:

```powershell
# Build Script for Water Balance Application

Write-Host "🔧 Starting build process..." -ForegroundColor Cyan

# Step 1: Clean
Write-Host "`n📦 Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build, dist, installer_output -ErrorAction SilentlyContinue

# Step 2: Build executable
Write-Host "`n🏗️  Building executable with PyInstaller..." -ForegroundColor Yellow
.venv\Scripts\python.exe -m PyInstaller water_balance.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ PyInstaller build failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Test executable
Write-Host "`n🧪 Testing executable..." -ForegroundColor Yellow
$testResult = Start-Process -FilePath "dist\WaterBalance\WaterBalance.exe" -PassThru -Wait -WindowStyle Hidden
if ($testResult.ExitCode -ne 0) {
    Write-Host "`n⚠️  Executable test returned non-zero exit code" -ForegroundColor Yellow
}

# Step 4: Create installer
Write-Host "`n📀 Creating installer with Inno Setup..." -ForegroundColor Yellow
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    & $innoPath installer.iss
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Build completed successfully!" -ForegroundColor Green
        Write-Host "`n📁 Output locations:" -ForegroundColor Cyan
        Write-Host "   Executable: dist\WaterBalance\" -ForegroundColor White
        Write-Host "   Installer: installer_output\WaterBalanceSetup_v1.0.0.exe" -ForegroundColor White
    } else {
        Write-Host "`n❌ Inno Setup compilation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n⚠️  Inno Setup not found. Skipping installer creation." -ForegroundColor Yellow
    Write-Host "   Download from: https://jrsoftware.org/isdl.php" -ForegroundColor White
}

Write-Host "`n🎉 Build process complete!" -ForegroundColor Green
```

Run with:
```powershell
.\build.ps1
```

---

## Troubleshooting

### PyInstaller Issues

**Problem**: Hidden import errors
```
Solution: Add missing modules to hiddenimports in water_balance.spec
```

**Problem**: Data files not included
```
Solution: Check datas list in water_balance.spec
```

**Problem**: Large executable size
```
Solution: Use --exclude-module for unused packages
```

### Inno Setup Issues

**Problem**: File not found errors
```
Solution: Verify Source paths in installer.iss match actual file locations
```

**Problem**: Permissions errors
```
Solution: Run as administrator or adjust PrivilegesRequired setting
```

### Runtime Issues

**Problem**: Application won't start
```
Solution: Run from command line to see error messages
dist\WaterBalance\WaterBalance.exe --debug
```

**Problem**: Missing DLLs
```
Solution: Copy from Python installation or add to binaries in spec file
```

---

## Distribution Checklist

- [ ] Application tested on clean machine
- [ ] All features verified working
- [ ] License activation tested
- [ ] Database creation successful
- [ ] Reports generate correctly
- [ ] Help documentation accessible
- [ ] Installer creates shortcuts correctly
- [ ] Uninstaller removes all files
- [ ] Version information correct
- [ ] Icon displays correctly

---

## Release Process

1. **Update version numbers** in:
   - `version_info.txt`
   - `installer.iss`
   - `water_balance.spec`
   - `CHANGELOG.md`

2. **Run full build**:
   ```powershell
   .\build.ps1
   ```

3. **Test installer** on multiple machines

4. **Create release package**:
   - Installer executable
   - README.md
   - LICENSE.txt
   - CHANGELOG.md

5. **Upload to distribution server**

6. **Notify users** of new version

---

_Last updated: January 14, 2026_
