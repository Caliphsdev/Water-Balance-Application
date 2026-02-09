$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Venv313 = Join-Path $ProjectRoot ".venv313\Scripts\python.exe"
$VenvDefault = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $Venv313) { $Venv313 } else { $VenvDefault }
$Spec = Join-Path $PSScriptRoot "water_balance.spec"

& $Python -m PyInstaller $Spec --clean
