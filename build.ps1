# Build Script for Water Balance Application
# Automated build process using PyInstaller and Inno Setup

Write-Host "🔧 Water Balance Application - Build Process" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Configuration
$ProjectRoot = "c:\PROJECTS\Water-Balance-Application"
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$Version = "1.0.0"

# Step 1: Clean previous builds
Write-Host "📦 Step 1: Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$ProjectRoot\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$ProjectRoot\dist" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$ProjectRoot\installer_output" -ErrorAction SilentlyContinue
Write-Host "   ✓ Cleaned build directories`n" -ForegroundColor Green

# Step 2: Verify Python environment
Write-Host "🐍 Step 2: Verifying Python environment..." -ForegroundColor Yellow
if (-not (Test-Path $VenvPython)) {
    Write-Host "   ❌ Virtual environment not found at: $VenvPython" -ForegroundColor Red
    exit 1
}
$pythonVersion = & $VenvPython --version
Write-Host "   ✓ Python environment found: $pythonVersion`n" -ForegroundColor Green

# Step 3: Install PyInstaller if needed
Write-Host "📦 Step 3: Checking PyInstaller..." -ForegroundColor Yellow
$pyinstallerCheck = & $VenvPython -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Installing PyInstaller..." -ForegroundColor Yellow
    & $VenvPython -m pip install pyinstaller --quiet
}
Write-Host "   ✓ PyInstaller ready`n" -ForegroundColor Green

# Step 4: Build executable with PyInstaller
Write-Host "🏗️  Step 4: Building executable..." -ForegroundColor Yellow
Write-Host "   This may take several minutes...`n" -ForegroundColor Gray
& $VenvPython -m PyInstaller "$ProjectRoot\water_balance.spec" --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n   ❌ PyInstaller build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Executable built successfully`n" -ForegroundColor Green

# Step 5: Verify executable exists
Write-Host "🔍 Step 5: Verifying build output..." -ForegroundColor Yellow
$exePath = "$ProjectRoot\dist\WaterBalance\WaterBalance.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "   ❌ Executable not found at: $exePath" -ForegroundColor Red
    exit 1
}
$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "   ✓ Executable found: $([math]::Round($exeSize, 2)) MB`n" -ForegroundColor Green

# Step 6: Create installer with Inno Setup
Write-Host "📀 Step 6: Creating Windows installer..." -ForegroundColor Yellow
if (Test-Path $InnoSetupPath) {
    & $InnoSetupPath "$ProjectRoot\installer.iss"
    
    if ($LASTEXITCODE -eq 0) {
        $installerPath = "$ProjectRoot\installer_output\WaterBalanceSetup_v$Version.exe"
        if (Test-Path $installerPath) {
            $installerSize = (Get-Item $installerPath).Length / 1MB
            Write-Host "   ✓ Installer created: $([math]::Round($installerSize, 2)) MB`n" -ForegroundColor Green
        }
    } else {
        Write-Host "   ❌ Inno Setup compilation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠️  Inno Setup not found at: $InnoSetupPath" -ForegroundColor Yellow
    Write-Host "   Skipping installer creation." -ForegroundColor Yellow
    Write-Host "   Download from: https://jrsoftware.org/isdl.php`n" -ForegroundColor White
}

# Step 7: Summary
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Build Process Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "📁 Output Locations:" -ForegroundColor Cyan
Write-Host "   Standalone Executable:" -ForegroundColor White
Write-Host "   → $ProjectRoot\dist\WaterBalance\`n" -ForegroundColor Gray

if (Test-Path "$ProjectRoot\installer_output\WaterBalanceSetup_v$Version.exe") {
    Write-Host "   Windows Installer:" -ForegroundColor White
    Write-Host "   → $ProjectRoot\installer_output\WaterBalanceSetup_v$Version.exe`n" -ForegroundColor Gray
}

Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Test the standalone executable" -ForegroundColor White
Write-Host "   2. Test the installer on a clean machine" -ForegroundColor White
Write-Host "   3. Verify license activation works" -ForegroundColor White
Write-Host "   4. Check all features function correctly" -ForegroundColor White
Write-Host "   5. Review logs for any errors`n" -ForegroundColor White

Write-Host "🎉 Ready for distribution!" -ForegroundColor Green
