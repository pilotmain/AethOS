# SPDX-License-Identifier: Apache-2.0
# Start the local AethOS API and Mission Control processes on Windows.
[CmdletBinding()]
param(
    [switch]$ApiOnly,
    [switch]$WebOnly,
    [switch]$NoReload,
    [int]$ApiPort = $(if ($env:AETHOS_API_PORT) { [int]$env:AETHOS_API_PORT } else { 8010 }),
    [int]$WebPort = $(if ($env:AETHOS_WEB_PORT) { [int]$env:AETHOS_WEB_PORT } else { 3000 }),
    [switch]$Help
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$processes = New-Object System.Collections.Generic.List[System.Diagnostics.Process]

function Write-AethOS([string]$Message) { Write-Host "[AethOS] $Message" -ForegroundColor Cyan }

if ($Help) {
    @"
Start AethOS locally

Usage: .\run.ps1 [options]

Options:
  -ApiOnly        Start only the API
  -WebOnly        Start only Mission Control
  -NoReload       Disable the API source reloader
  -ApiPort PORT   API port (default: 8010)
  -WebPort PORT   Mission Control port (default: 3000)
  -Help           Show this help

Press Ctrl+C to stop every process started by this command.
"@ | Write-Host
    exit 0
}

if ($ApiOnly -and $WebOnly) { throw "-ApiOnly and -WebOnly cannot be used together." }
$startApi = -not $WebOnly
$startWeb = -not $ApiOnly
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if ($startApi -and -not (Test-Path $venvPython)) {
    throw "Python environment missing. Run .\install.ps1 -Resume first."
}
if ($startWeb) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm is missing. Run .\install.ps1 -HelpStep preflight."
    }
    if (-not (Test-Path (Join-Path $root "web\node_modules"))) {
        throw "Mission Control dependencies missing. Run .\install.ps1 -From frontend."
    }
}

# -- Version gate -------------------------------------------------------------
# Warns when a newer release exists; blocks startup once an update has been
# available for AETHOS_VERSION_GATE_DAYS (default 30). .\install.ps1 -Update fixes it.
function Test-AethOSUpdates {
    if ($env:AETHOS_SKIP_UPDATE_CHECK -eq "1") { return }
    $versionFile = Join-Path $root "VERSION"
    $current = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "0.0.0" }
    $gateDays = if ($env:AETHOS_VERSION_GATE_DAYS) { [int]$env:AETHOS_VERSION_GATE_DAYS } else { 30 }
    $stateDir = Join-Path $root ".aethos-installer"
    $cache = Join-Path $stateDir "update-check"
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $latest = ""; $checkedAt = 0; $firstSeen = 0
    if (Test-Path $cache) {
        foreach ($line in Get-Content $cache) {
            if ($line -match "^latest=(.*)$") { $latest = $Matches[1] }
            elseif ($line -match "^checked_at=(\d+)$") { $checkedAt = [long]$Matches[1] }
            elseif ($line -match "^first_seen=(\d+)$") { $firstSeen = [long]$Matches[1] }
        }
    }
    if (($now - $checkedAt) -gt 86400) {
        try {
            $release = Invoke-RestMethod -Uri "https://api.github.com/repos/pilotmain/AethOS/releases/latest" -TimeoutSec 6 -UseBasicParsing
            $fetched = ($release.tag_name -replace "^v", "")
            if ($fetched -match "^\d+\.\d+") { $latest = $fetched; $checkedAt = $now }
        }
        catch { }
    }
    if (-not $latest) { return }
    $newer = $false
    try { $newer = [version]$current -lt [version]$latest } catch { }
    if ($newer) {
        if ($firstSeen -eq 0) { $firstSeen = $now }
        $days = [int](($now - $firstSeen) / 86400)
        @("latest=$latest", "checked_at=$checkedAt", "first_seen=$firstSeen") | Set-Content -Encoding UTF8 $cache
        if ($days -ge $gateDays) {
            Write-Host "[AethOS] Update required." -ForegroundColor Red
            Write-Host "         Version $current is installed; $latest has been available for $days days (limit: $gateDays)."
            Write-Host "         To keep local installs current and safe, AethOS will not start until it is updated:"
            Write-Host "             cd `"$root`"; .\install.ps1 -Update"
            Write-Host "         Broken install? Reinstall fresh (your .env can be kept): .\install.ps1 -Reinstall"
            exit 1
        }
        Write-AethOS "Update available: v$current -> v$latest. Run: .\install.ps1 -Update ($($gateDays - $days) days before updating is required)"
    }
    else {
        @("latest=$latest", "checked_at=$checkedAt", "first_seen=0") | Set-Content -Encoding UTF8 $cache
    }
}

Test-AethOSUpdates

Write-Host ""
Write-Host "  AethOS Mission Control" -ForegroundColor Cyan
Write-Host "  Governed local runtime" -ForegroundColor DarkGray
Write-Host ""

try {
    if ($startApi) {
        Write-AethOS "API -> http://127.0.0.1:$ApiPort"
        $apiArgs = @("-m", "uvicorn", "aethos_core.api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort")
        if (-not $NoReload -and $env:AETHOS_NO_RELOAD -ne "1") {
            $apiArgs += @("--reload", "--reload-dir", "aethos_core", "--reload-exclude", "data/*", "--reload-exclude", "*.json", "--reload-exclude", "*.log")
        }
        $api = Start-Process -FilePath $venvPython -ArgumentList $apiArgs -WorkingDirectory $root -NoNewWindow -PassThru
        $processes.Add($api)
    }
    if ($startWeb) {
        Write-AethOS "UI  -> http://localhost:$WebPort"
        $npm = (Get-Command npm).Source
        $web = Start-Process -FilePath $npm -ArgumentList @("run", "dev", "--", "--port", "$WebPort") -WorkingDirectory (Join-Path $root "web") -NoNewWindow -PassThru
        $processes.Add($web)
    }
    Write-Host ""
    Write-Host "[AethOS] Runtime active. Press Ctrl+C to stop." -ForegroundColor Green
    Write-Host ""
    while ($true) {
        Start-Sleep -Milliseconds 500
        foreach ($process in $processes) {
            if ($process.HasExited) { throw "AethOS process $($process.Id) exited with code $($process.ExitCode)." }
        }
    }
}
finally {
    Write-AethOS "Shutting down..."
    foreach ($process in $processes) {
        if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    }
}
