$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$VenvDefault = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = $VenvDefault
$Spec = Join-Path $PSScriptRoot "water_balance.spec"
$RccSource = Join-Path $ProjectRoot "src\ui\resources\resources.qrc"
$RccOutput = Join-Path $ProjectRoot "src\ui\resources\resources_rc.py"
$RccTool = Join-Path (Split-Path $Python -Parent) "pyside6-rcc.exe"

if (-not (Test-Path $Python)) {
	throw "Expected packaging Python at $Python. Create/activate .venv first."
}

# Verify runtime-critical packages in the same env used for packaging.
& $Python -c "import pandas, openpyxl, xlrd, PySide6; print('packaging-env-ok')"
if ($LASTEXITCODE -ne 0) {
	throw "Missing required packages in .venv (need pandas, openpyxl, xlrd, PySide6)."
}

$DistDir = Join-Path $ProjectRoot "dist\WaterBalanceDashboard"
$BuildDir = Join-Path $ProjectRoot "build"
if (Test-Path $DistDir) {
	Remove-Item -Path $DistDir -Recurse -Force
}
if (Test-Path $BuildDir) {
	Remove-Item -Path $BuildDir -Recurse -Force
}

# Rebuild Qt resources before packaging so latest icons/images are embedded
if (-not (Test-Path $RccTool)) {
	throw "pyside6-rcc not found at $RccTool"
}
& $RccTool "$RccSource" -o "$RccOutput"

& $Python -m PyInstaller $Spec --clean
