# SPDX-License-Identifier: Apache-2.0
# AethOS installer for Windows PowerShell 5.1+ and PowerShell 7+.
[CmdletBinding()]
param(
    [switch]$Resume,
    [switch]$Status,
    [ValidateSet("preflight", "source", "backend", "frontend", "verify")]
    [string]$From,
    [ValidateSet("preflight", "source", "backend", "frontend", "verify")]
    [string]$HelpStep,
    [string]$InstallDir = $(if ($env:AETHOS_INSTALL_DIR) { $env:AETHOS_INSTALL_DIR } else { Join-Path $HOME "aethos" }),
    [string]$Branch = $(if ($env:AETHOS_BRANCH) { $env:AETHOS_BRANCH } else { "main" }),
    [int]$ApiPort = $(if ($env:AETHOS_API_PORT) { [int]$env:AETHOS_API_PORT } else { 8010 }),
    [int]$WebPort = $(if ($env:AETHOS_WEB_PORT) { [int]$env:AETHOS_WEB_PORT } else { 3000 }),
    [switch]$SkipWeb,
    [switch]$Detailed,
    [switch]$Help
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$script:AethOSVersion = "0.2.0"
$script:RepoUrl = if ($env:AETHOS_REPO_URL) { $env:AETHOS_REPO_URL } else { "https://github.com/pilotmain/AethOS.git" }
$script:InstallerUrl = if ($env:AETHOS_INSTALLER_URL) { $env:AETHOS_INSTALLER_URL } else { "https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1" }
$script:MinPython = [version]"3.11"
$script:MinNode = [version]"20.0"
$script:RecommendedNode = [version]"24.0"
$script:Steps = @("preflight", "source", "backend", "frontend", "verify")
$script:CurrentStep = "startup"
$script:Root = $null
$script:PythonCommand = $null
$script:PythonPrefix = @()
$script:StateDir = $null
$script:LogFile = $null

function Write-AethOS([string]$Message) { Write-Host "[AethOS] $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "[AethOS] $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[AethOS] $Message" -ForegroundColor Yellow }
function Write-Fail([string]$Message) { Write-Host "[AethOS] $Message" -ForegroundColor Red }
function Write-Note([string]$Message) { Write-Host "         $Message" -ForegroundColor DarkGray }
function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host $Title -ForegroundColor Cyan
}

function Show-Usage {
    @"
AethOS installer - Windows PowerShell

Usage:
  .\install.ps1 [options]
  irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | iex

Options:
  -Resume                 Continue after the last completed step
  -From STEP              Re-run STEP and every step after it
  -Status                 Show prerequisites and saved install progress
  -HelpStep STEP          Explain a step and its recovery actions
  -InstallDir PATH        Install location (default: ~/aethos)
  -Branch NAME            Git branch or tag (default: main)
  -ApiPort PORT           API port (default: 8010)
  -WebPort PORT           Mission Control port (default: 3000)
  -SkipWeb                Install the API and CLI without Mission Control
  -Detailed               Show full pip and npm output
  -Help                    Show this help

Steps: preflight, source, backend, frontend, verify
"@ | Write-Host
}

function Show-StepHelp([string]$Step) {
    switch ($Step) {
        "preflight" {
            Write-Host "preflight checks disk space, Git, Python 3.11+, and Node 20+ (Node 24 LTS recommended)."
            Write-Host "It never installs system packages or changes PATH. Install missing tools from the official"
            Write-Host "vendors or with winget, open a new PowerShell window, and re-run with -Resume."
        }
        "source" {
            Write-Host "source uses the current AethOS checkout when run inside one; otherwise it clones"
            Write-Host "$($script:RepoUrl) into $InstallDir. Existing local changes are never overwritten."
        }
        "backend" {
            Write-Host "backend creates .venv, installs AethOS with cloud and secure-vault support, and"
            Write-Host "creates .env only when it is missing. Existing credentials are never overwritten."
        }
        "frontend" {
            Write-Host "frontend uses npm ci to install the locked Mission Control dependency graph and"
            Write-Host "creates web/.env.local only when missing. Use -SkipWeb for API/CLI only."
        }
        "verify" {
            Write-Host "verify imports the API, exercises the CLI, and checks Mission Control types."
            Write-Host "It does not start services or contact any configured provider."
        }
    }
}

function Show-Banner {
    Write-Host ""
    Write-Host "     A E T H O S  v$($script:AethOSVersion)" -ForegroundColor Cyan
    Write-Host "     Governed operations. Evidence before action." -ForegroundColor DarkGray
    Write-Host "     Local-first | resumable | safe by default" -ForegroundColor DarkGray
    Write-Host ""
}

function Initialize-State {
    $existing = Find-ExistingRoot
    if ($env:AETHOS_STATE_DIR) { $stateRoot = $env:AETHOS_STATE_DIR }
    elseif ($existing) { $stateRoot = Join-Path $existing ".aethos-installer" }
    else { $stateRoot = "$InstallDir.installer" }
    $script:StateDir = Join-Path $stateRoot "v$($script:AethOSVersion)"
    New-Item -ItemType Directory -Force -Path $script:StateDir | Out-Null
    $script:LogFile = Join-Path $script:StateDir "install.log"
    if (-not (Test-Path $script:LogFile)) { New-Item -ItemType File -Path $script:LogFile | Out-Null }
}

function Get-Marker([string]$Step) { Join-Path $script:StateDir "$Step.done" }
function Test-StepDone([string]$Step) { Test-Path (Get-Marker $Step) }
function Set-StepDone([string]$Step) { [DateTime]::UtcNow.ToString("o") | Set-Content -Encoding UTF8 (Get-Marker $Step) }

function Get-ResumeCommand {
    $escaped = $InstallDir.Replace("'", "''")
    $localInstaller = Join-Path $InstallDir "install.ps1"
    if (Test-Path $localInstaller) { return "cd '$escaped'; .\install.ps1 -Resume" }
    "& ([scriptblock]::Create((irm '$($script:InstallerUrl)'))) -Resume -InstallDir '$escaped'"
}

function Get-StepHelpCommand {
    $escaped = $InstallDir.Replace("'", "''")
    $localInstaller = Join-Path $InstallDir "install.ps1"
    if (Test-Path $localInstaller) { return "cd '$escaped'; .\install.ps1 -HelpStep $($script:CurrentStep)" }
    "& ([scriptblock]::Create((irm '$($script:InstallerUrl)'))) -HelpStep $($script:CurrentStep)"
}

function Stop-Install([object]$Failure) {
    Write-Host ""
    Write-Fail "Installation stopped during '$($script:CurrentStep)'."
    Write-Note "Nothing completed earlier was rolled back or overwritten."
    Write-Note "Step help: $(Get-StepHelpCommand)"
    Write-Note "Continue:  $(Get-ResumeCommand)"
    Write-Note "Log:       $($script:LogFile)"
    if ($Detailed -and $Failure) { Write-Host $Failure -ForegroundColor DarkRed }
}

function Invoke-Native([string]$Command, [string[]]$Arguments) {
    if ($Detailed) {
        & $Command @Arguments
    }
    else {
        & $Command @Arguments 2>&1 | Out-File -FilePath $script:LogFile -Append -Encoding utf8
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Command failed: $Command $($Arguments -join ' ')"
        Write-Note "Last log lines:"
        if (Test-Path $script:LogFile) { Get-Content $script:LogFile -Tail 35 | Write-Host }
        throw "Native command exited with $LASTEXITCODE"
    }
}

function Resolve-Python {
    foreach ($candidate in @("py", "python", "python3")) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $found) { continue }
        $prefix = if ($candidate -eq "py") { @("-3") } else { @() }
        try {
            $versionText = (& $found.Source @prefix -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null).Trim()
            if ([version]$versionText -ge $script:MinPython) {
                $script:PythonCommand = $found.Source
                $script:PythonPrefix = $prefix
                return $versionText
            }
        }
        catch { continue }
    }
    return $null
}

function Invoke-Python([string[]]$Arguments) {
    $allArguments = @($script:PythonPrefix + $Arguments)
    Invoke-Native -Command $script:PythonCommand -Arguments $allArguments
}

function Find-ExistingRoot {
    $candidates = New-Object System.Collections.Generic.List[string]
    $candidates.Add((Get-Location).Path)
    if ($PSScriptRoot) { $candidates.Add($PSScriptRoot) }
    $candidates.Add([IO.Path]::GetFullPath($InstallDir))
    foreach ($candidate in $candidates) {
        $project = Join-Path $candidate "pyproject.toml"
        if ((Test-Path $project) -and (Select-String -Path $project -Pattern '^name\s*=\s*"aethos"' -Quiet)) {
            return $candidate
        }
    }
    return $null
}

function Invoke-Preflight {
    Write-Section "1 / 5  Preflight"
    $missing = $false
    Write-Ok "Windows detected"

    $existing = Find-ExistingRoot
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git -and -not $existing) {
        Write-Fail "Git is required to download AethOS."
        $missing = $true
    }
    elseif ($git) { Write-Ok "Git $((& $git.Source --version) -replace '^git version ', '')" }
    else { Write-Ok "Local source detected; Git is optional for this run" }

    $pythonVersion = Resolve-Python
    if ($pythonVersion) { Write-Ok "Python $pythonVersion" }
    else {
        Write-Fail "Python 3.11+ is required."
        $missing = $true
    }

    if ($SkipWeb) { Write-Note "Mission Control skipped by request" }
    else {
        $node = Get-Command node -ErrorAction SilentlyContinue
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $node -or -not $npm) {
            Write-Fail "Node.js 20+ and npm are required for Mission Control."
            $missing = $true
        }
        else {
            $nodeVersion = [version]((& $node.Source --version).TrimStart("v"))
            if ($nodeVersion -lt $script:MinNode) {
                Write-Fail "Node.js 20+ is required; found $nodeVersion."
                $missing = $true
            }
            else {
                Write-Ok "Node $nodeVersion with npm $(& $npm.Source --version)"
                if ($nodeVersion -lt $script:RecommendedNode) { Write-Warn "Node 24 LTS is recommended for the public release path" }
            }
        }
    }

    $drive = Get-Item ([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($InstallDir)))
    if ($drive.PSDrive.Free -lt 1GB) {
        Write-Fail "At least 1 GB of free disk space is required."
        $missing = $true
    }
    else { Write-Ok "Disk space check passed" }

    if ($missing) {
        Write-Note "Windows help: https://github.com/pilotmain/AethOS/blob/main/docs/GETTING_STARTED.md#windows-prerequisites"
        Write-Note "With winget: winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS"
        throw "Missing prerequisites"
    }
    Write-Note "Mutation execution and host shell access remain disabled by default."
}

function Invoke-Source {
    Write-Section "2 / 5  Source"
    $script:Root = Find-ExistingRoot
    if ($script:Root) {
        Write-Ok "Using existing AethOS source: $($script:Root)"
        return
    }

    if ((Test-Path $InstallDir) -and -not (Test-Path (Join-Path $InstallDir ".git"))) {
        throw "Install path exists but is not an AethOS Git checkout: $InstallDir"
    }
    if (Test-Path (Join-Path $InstallDir ".git")) {
        $script:Root = [IO.Path]::GetFullPath($InstallDir)
        $changes = & git -C $script:Root status --porcelain
        if ($changes) { Write-Warn "Existing checkout has local changes; source update skipped" }
        else {
            Write-AethOS "Updating existing checkout without rewriting history..."
            Invoke-Native "git" @("-C", $script:Root, "fetch", "--depth", "1", "origin", $Branch)
            Invoke-Native "git" @("-C", $script:Root, "checkout", $Branch)
            Invoke-Native "git" @("-C", $script:Root, "merge", "--ff-only", "origin/$Branch")
        }
    }
    else {
        Write-AethOS "Cloning AethOS into $InstallDir..."
        $parent = Split-Path -Parent ([IO.Path]::GetFullPath($InstallDir))
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Invoke-Native "git" @("clone", "--depth", "1", "--branch", $Branch, $script:RepoUrl, $InstallDir)
        $script:Root = [IO.Path]::GetFullPath($InstallDir)
    }
    Write-Ok "Source ready at $($script:Root)"
}

function Assert-Root {
    if (-not $script:Root) { $script:Root = Find-ExistingRoot }
    if (-not $script:Root -or -not (Test-Path (Join-Path $script:Root "pyproject.toml"))) {
        throw "AethOS source is unavailable; re-run from the source step."
    }
}

function Invoke-Backend {
    Write-Section "3 / 5  Backend and CLI"
    Assert-Root
    if (-not (Resolve-Python)) { throw "Python 3.11+ is no longer available." }
    Push-Location $script:Root
    try {
        $venvPython = Join-Path $script:Root ".venv\Scripts\python.exe"
        if (-not (Test-Path $venvPython)) {
            Write-AethOS "Creating an isolated Python environment..."
            Invoke-Python @("-m", "venv", ".venv")
        }
        else { Write-Ok "Python environment already exists" }
        Write-AethOS "Installing AethOS, cloud adapters, and secure-vault support..."
        Invoke-Native $venvPython @("-m", "pip", "install", "--upgrade", "pip")
        Invoke-Native $venvPython @("-m", "pip", "install", "-c", "requirements.lock", "-e", ".[cloud,secrets]")
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Ok "Created .env from the safe-default template"
        }
        else { Write-Ok "Preserved existing .env" }
        Write-Ok "API and CLI installed"
    }
    finally { Pop-Location }
}

function Invoke-Frontend {
    Write-Section "4 / 5  Mission Control"
    if ($SkipWeb) { Write-Note "Skipped by -SkipWeb"; return }
    Assert-Root
    $webDir = Join-Path $script:Root "web"
    Push-Location $webDir
    try {
        if (-not (Test-Path ".env.local")) {
            @(
                "# Same-origin /api/v1 proxy is recommended for auth cookies.",
                "# NEXT_PUBLIC_API_BASE=http://127.0.0.1:$ApiPort"
            ) | Set-Content -Encoding UTF8 ".env.local"
            Write-Ok "Created web/.env.local"
        }
        else { Write-Ok "Preserved existing web/.env.local" }
        $npm = (Get-Command npm -ErrorAction Stop).Source
        Write-AethOS "Installing the locked Mission Control dependency graph..."
        Invoke-Native $npm @("ci", "--no-audit", "--no-fund")
        Write-Ok "Mission Control dependencies installed"
    }
    finally { Pop-Location }
}

function Invoke-Verify {
    Write-Section "5 / 5  Verification"
    Assert-Root
    $venvPython = Join-Path $script:Root ".venv\Scripts\python.exe"
    $aethosCli = Join-Path $script:Root ".venv\Scripts\aethos.exe"
    Push-Location $script:Root
    try {
        Write-AethOS "Checking the installed API and CLI..."
        Invoke-Native $venvPython @("-c", "import aethos_core; from aethos_core.api.main import app; assert app")
        Invoke-Native $aethosCli @("--help")
        if (-not $SkipWeb) {
            if (-not (Test-Path "web\node_modules\.bin\next.cmd")) { throw "Mission Control dependency check failed." }
            Write-AethOS "Checking Mission Control types..."
            Push-Location "web"
            try { Invoke-Native (Get-Command npm).Source @("run", "typecheck") }
            finally { Pop-Location }
        }
        Write-Ok "Local installation verified"
    }
    finally { Pop-Location }
}

function Invoke-Steps {
    $fromIndex = -1
    if ($From) { $fromIndex = [Array]::IndexOf($script:Steps, $From) }
    for ($index = 0; $index -lt $script:Steps.Count; $index++) {
        $step = $script:Steps[$index]
        if ($fromIndex -ge 0 -and $index -lt $fromIndex) {
            Write-Note "Skipping $step; -From starts at $From"
            continue
        }
        if ($Resume -and $fromIndex -lt 0 -and (Test-StepDone $step)) {
            Write-Ok "$step already complete"
            continue
        }
        $script:CurrentStep = $step
        switch ($step) {
            "preflight" { Invoke-Preflight }
            "source" { Invoke-Source }
            "backend" { Invoke-Backend }
            "frontend" { Invoke-Frontend }
            "verify" { Invoke-Verify }
        }
        Set-StepDone $step
    }
}

function Show-Status {
    Show-Banner
    Write-Section "Install status"
    Write-Host ("  {0,-12} {1}" -f "Install dir", $InstallDir)
    Write-Host ("  {0,-12} {1}" -f "Version", $script:AethOSVersion)
    Write-Host ("  {0,-12} {1}" -f "State", $script:StateDir)
    Write-Host ""
    foreach ($step in $script:Steps) {
        if (Test-StepDone $step) { Write-Ok ("{0,-10} complete" -f $step) }
        else { Write-Note ("{0,-10} pending" -f $step) }
    }
    Write-Host ""
    if (Get-Command git -ErrorAction SilentlyContinue) { Write-Ok "Git available" } else { Write-Warn "Git not found" }
    $pythonVersion = Resolve-Python
    if ($pythonVersion) { Write-Ok "Python $pythonVersion" } else { Write-Warn "Python 3.11+ not found" }
    if (Get-Command node -ErrorAction SilentlyContinue) { Write-Ok "Node $(& node --version)" } else { Write-Warn "Node not found" }
    Write-Note "Continue: $(Get-ResumeCommand)"
}

function Show-Success {
    Write-Section "AethOS is ready"
    Write-Ok "Installation and local verification completed."
    Write-Host ""
    Write-Host "  Start             cd `"$($script:Root)`"; .\run.ps1"
    Write-Host "  Mission Control   http://localhost:$WebPort"
    Write-Host "  API health        http://127.0.0.1:$ApiPort/api/v1/health"
    Write-Host "  Doctor            .\.venv\Scripts\aethos.exe doctor"
    Write-Host ""
    Write-Host "  AI provider       Set USE_REAL_LLM=true and at least one key in `"$($script:Root)\.env`""
    Write-Note "Supported: Anthropic / OpenRouter / OpenAI / Gemini / Mistral / Groq / xAI / DeepSeek / Together / local (Ollama, LM Studio)"
    Write-Host ""
    Write-Note "Installer status: .\install.ps1 -Status"
    Write-Note "Step help:        .\install.ps1 -HelpStep STEP"
    Write-Note "Detailed log:     $($script:LogFile)"
    Write-Note "Mutation execution and host shell access are still disabled."
}

if ($Help) { Show-Usage; exit 0 }
if ($HelpStep) { Show-StepHelp $HelpStep; exit 0 }
Initialize-State
if ($Status) { Show-Status; exit 0 }

try {
    Show-Banner
    Write-Note "Progress is checkpointed; a failed run can continue with -Resume."
    Invoke-Steps
    $script:CurrentStep = "complete"
    Show-Success
}
catch {
    Stop-Install $_
    exit 1
}
