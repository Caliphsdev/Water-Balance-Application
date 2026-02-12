$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Venv313 = Join-Path $ProjectRoot ".venv313\Scripts\python.exe"
$VenvDefault = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $Venv313) { $Venv313 } else { $VenvDefault }
$Spec = Join-Path $PSScriptRoot "water_balance.spec"
$RccSource = Join-Path $ProjectRoot "src\ui\resources\resources.qrc"
$RccOutput = Join-Path $ProjectRoot "src\ui\resources\resources_rc.py"
$RccTool = Join-Path (Split-Path $Python -Parent) "pyside6-rcc.exe"

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
