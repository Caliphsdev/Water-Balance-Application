param(
    [switch]$SupabaseOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ConfigPath = Join-Path $ProjectRoot "config\app_config.yaml"
$IssPath = Join-Path $PSScriptRoot "water_balance.iss"
$BuildScript = Join-Path $PSScriptRoot "build_windows.ps1"
$InstallerPath = Join-Path $PSScriptRoot "dist\installer\WaterBalanceDashboard-Setup.exe"

$AllowedTiers = @("developer", "premium", "standard", "free_trial", "customer")

function Get-ConfigVersion {
    param([string]$Path)
    $line = (Get-Content $Path | Where-Object { $_ -match "^\s*version:\s*" } | Select-Object -First 1)
    if (-not $line) { return "" }
    return ($line -replace "^\s*version:\s*", "").Trim()
}

function Set-ConfigVersion {
    param([string]$Path, [string]$Version)
    $content = Get-Content $Path
    $content = $content | ForEach-Object {
        if ($_ -match "^\s*version:\s*") {
            "  version: $Version"
        } else {
            $_
        }
    }
    Set-Content -Path $Path -Value $content
}

function Set-IssVersion {
    param([string]$Path, [string]$Version)
    $content = Get-Content $Path
    $content = $content | ForEach-Object {
        if ($_ -match "^#define AppVersion") {
            "#define AppVersion \"$Version\""
        } else {
            $_
        }
    }
    Set-Content -Path $Path -Value $content
}

function Get-InstallerMetadata {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Installer not found at $Path"
    }
    $hash = (Get-FileHash -Algorithm SHA256 $Path).Hash
    $size = (Get-Item $Path).Length
    return @{ Hash = $hash; Size = $size }
}

function Read-Required {
    param([string]$Prompt, [string]$Default = "")
    $value = Read-Host $Prompt
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }
    return $value
}

$currentVersion = Get-ConfigVersion -Path $ConfigPath
$mode = if ($SupabaseOnly) { "supabase" } else { "full" }

if (-not $SupabaseOnly) {
    $modeInput = Read-Host "Release mode: full or supabase-only [full]"
    if (-not [string]::IsNullOrWhiteSpace($modeInput)) {
        $mode = $modeInput.Trim().ToLowerInvariant()
    }
}

$versionPrompt = "Version (e.g., 1.0.9) [$currentVersion]"
$version = Read-Required -Prompt $versionPrompt -Default $currentVersion
$releaseNotes = Read-Required -Prompt "Release notes" -Default "bug fixes and design improvements"

$tiersInput = Read-Required -Prompt "Min tiers (comma-separated) [developer]" -Default "developer"
$tiers = $tiersInput.Split(",") | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ -ne "" }
$invalidTiers = $tiers | Where-Object { $AllowedTiers -notcontains $_ }
if ($invalidTiers.Count -gt 0) {
    throw "Invalid tiers: $($invalidTiers -join ", ")"
}

$mandatoryInput = Read-Required -Prompt "Is mandatory update? (y/n) [n]" -Default "n"
$isMandatory = $mandatoryInput.Trim().ToLowerInvariant() -eq "y"

if ($mode -ne "supabase" -and $mode -ne "full") {
    throw "Unknown mode: $mode"
}

if ($mode -eq "full") {
    if ([string]::IsNullOrWhiteSpace($version)) {
        throw "Version is required for full release."
    }

    Set-ConfigVersion -Path $ConfigPath -Version $version
    Set-IssVersion -Path $IssPath -Version $version

    & $BuildScript

    $issCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $issCompiler)) {
        throw "Inno Setup compiler not found at $issCompiler"
    }
    & $issCompiler $IssPath
}

$metadata = Get-InstallerMetadata -Path $InstallerPath
$downloadUrl = "https://github.com/Caliphsdev/Water-Balance-Application/releases/download/v$version/WaterBalanceDashboard-Setup.exe"

if ($mode -eq "full") {
    $tag = "v$version"
    & gh release create $tag $InstallerPath -t $tag -n $releaseNotes
}

$SupabaseUrl = $env:SUPABASE_URL
$SupabaseKey = $env:SUPABASE_SERVICE_ROLE_KEY

if ([string]::IsNullOrWhiteSpace($SupabaseUrl) -or [string]::IsNullOrWhiteSpace($SupabaseKey)) {
    throw "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables."
}

$payload = [ordered]@{
    version = $version
    min_tiers = $tiers
    download_url = $downloadUrl
    release_notes = $releaseNotes
    file_hash = $metadata.Hash
    file_size = $metadata.Size
    is_mandatory = $isMandatory
}

$headers = @{ 
    "apikey" = $SupabaseKey
    "Authorization" = "Bearer $SupabaseKey"
    "Content-Type" = "application/json"
    "Prefer" = "resolution=merge-duplicates,return=representation"
}

$body = $payload | ConvertTo-Json -Depth 5
$uri = "$SupabaseUrl/rest/v1/app_updates?on_conflict=version"

Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body

Write-Host "Release pipeline finished."
Write-Host "Version: $version"
Write-Host "Tiers: $($tiers -join ', ')"
Write-Host "Installer: $InstallerPath"
Write-Host "SHA256: $($metadata.Hash)"
Write-Host "Size: $($metadata.Size)"
