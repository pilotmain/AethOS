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
