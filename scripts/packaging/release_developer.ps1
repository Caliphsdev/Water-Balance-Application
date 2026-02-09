$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $scriptDir "release-$timestamp.log"

Start-Transcript -Path $logPath
try {
    $releaseScript = Join-Path $scriptDir "release.ps1"
    & $releaseScript
} finally {
    Stop-Transcript
    Write-Host "Release log saved to: $logPath"
}
