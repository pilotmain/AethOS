# SPDX-License-Identifier: Apache-2.0
# AethOS installer for Windows PowerShell 5.1+ and PowerShell 7+.
[CmdletBinding()]
param(
    [switch]$Resume,
    [switch]$Status,
    [switch]$Update,
    [switch]$Reinstall,
    [switch]$Uninstall,
    [switch]$Onboard,
    [switch]$NoOnboard,
    [switch]$NoStart,
    [switch]$NonInteractive,
    [switch]$Yes,
    [ValidateSet("preflight", "source", "backend", "frontend", "verify", "setup")]
    [string]$From,
    [ValidateSet("preflight", "source", "backend", "frontend", "verify", "setup")]
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

$script:AethOSVersion = "0.2.1"
$script:RepoUrl = if ($env:AETHOS_REPO_URL) { $env:AETHOS_REPO_URL } else { "https://github.com/pilotmain/AethOS.git" }
$script:InstallerUrl = if ($env:AETHOS_INSTALLER_URL) { $env:AETHOS_INSTALLER_URL } else { "https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1" }
$script:MinPython = [version]"3.11"
$script:MinNode = [version]"20.0"
$script:RecommendedNode = [version]"24.0"
$script:Steps = @("preflight", "source", "backend", "frontend", "verify", "setup")
$script:RestoreEnv = $null
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
  -Update                 Update an existing install to the latest version
  -Reinstall              Remove the existing install and install fresh
  -Uninstall              Remove the AethOS install from this machine
  -Onboard                (Re)run only the interactive setup wizard
  -NoOnboard              Skip the interactive setup wizard
  -NoStart                Do not launch AethOS after a successful install
  -NonInteractive         Never prompt; use safe defaults (CI/automation)
  -Yes                    Assume "yes" for confirmations
  -InstallDir PATH        Install location (default: ~/aethos)
  -Branch NAME            Git branch or tag (default: main)
  -ApiPort PORT           API port (default: 8010)
  -WebPort PORT           Mission Control port (default: 3000)
  -SkipWeb                Install the API and CLI without Mission Control
  -Detailed               Show full pip and npm output
  -Help                    Show this help

Steps: preflight, source, backend, frontend, verify, setup
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
        "setup" {
            Write-Host "setup is the interactive onboarding wizard: deployment mode, optional login"
            Write-Host "passphrase, and AI provider keys (validated live), all written to .env."
            Write-Host "Re-run any time with -Onboard; skip with -NoOnboard (CI skips automatically)."
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
    Write-Section "1 / 6  Preflight"
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
    Write-Section "2 / 6  Source"
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
    Write-Section "3 / 6  Backend and CLI"
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
            if ($script:RestoreEnv -and (Test-Path $script:RestoreEnv)) {
                Copy-Item $script:RestoreEnv ".env"
                Remove-Item $script:RestoreEnv -Force -ErrorAction SilentlyContinue
                Write-Ok "Restored your previous .env configuration"
            }
            else {
                Copy-Item ".env.example" ".env"
                Write-Ok "Created .env from the safe-default template"
            }
        }
        else { Write-Ok "Preserved existing .env" }
        Write-Ok "API and CLI installed"
    }
    finally { Pop-Location }
}

function Invoke-Frontend {
    Write-Section "4 / 6  Mission Control"
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
    Write-Section "5 / 6  Verification"
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
            if ($Detailed) {
                Write-AethOS "Checking Mission Control types (this can take a minute)..."
                Push-Location "web"
                try { Invoke-Native (Get-Command npm).Source @("run", "typecheck") }
                finally { Pop-Location }
            }
            else {
                Write-AethOS "Checking the Mission Control toolchain..."
                Invoke-Native (Get-Command node).Source @("-e", "require('./web/node_modules/next/package.json').version")
                Write-Note "Full typecheck runs in CI; use -Detailed to run it locally."
            }
        }
        Write-Ok "Local installation verified"
    }
    finally { Pop-Location }
}

# -- Interactive setup (onboarding) ------------------------------------------

function Test-Interactive {
    if ($NonInteractive -or $env:AETHOS_NONINTERACTIVE) { return $false }
    try { return -not [Console]::IsInputRedirected } catch { return $false }
}

function Read-AethOSInput([string]$Prompt, [string]$Default = "") {
    if (-not (Test-Interactive)) { return $Default }
    $label = if ($Default) { "  $Prompt [$Default]" } else { "  $Prompt" }
    $answer = Read-Host -Prompt $label
    if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
    return $answer.Trim()
}

function Read-AethOSSecret([string]$Prompt) {
    if (-not (Test-Interactive)) { return "" }
    $secure = Read-Host -Prompt "  $Prompt (hidden)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Confirm-AethOS([string]$Prompt, [string]$Default = "y") {
    if ($Yes) { return $true }
    if (-not (Test-Interactive)) { return ($Default -eq "y") }
    $suffix = if ($Default -eq "y") { "[Y/n]" } else { "[y/N]" }
    $answer = Read-AethOSInput "$Prompt $suffix" $Default
    return $answer -match "^[Yy]"
}

function Set-EnvValue([string]$Key, [string]$Value) {
    $envPath = Join-Path $script:Root ".env"
    $text = if (Test-Path $envPath) { Get-Content -Raw $envPath } else { "" }
    $pattern = "(?m)^#?\s*" + [regex]::Escape($Key) + "=.*$"
    $line = "$Key=$Value"
    if ($text -match $pattern) {
        $regex = [regex]::new($pattern)
        $text = $regex.Replace($text, $line, 1)
    }
    else {
        if ($text -and -not $text.EndsWith("`n")) { $text += "`n" }
        $text += "$line`n"
    }
    Set-Content -Path $envPath -Value $text -Encoding UTF8 -NoNewline
}

function Test-EnvHas([string]$Key) {
    $envPath = Join-Path $script:Root ".env"
    if (-not (Test-Path $envPath)) { return $false }
    return [bool](Select-String -Path $envPath -Pattern ("^" + [regex]::Escape($Key) + "=.+") -Quiet)
}

$script:Providers = @(
    @{ Id = "anthropic";  Label = "Anthropic (Claude)";                Model = "claude-sonnet-4-6";    Url = "https://console.anthropic.com/settings/keys"; Probe = "https://api.anthropic.com/v1/models" },
    @{ Id = "openrouter"; Label = "OpenRouter (one key, many models)"; Model = "openrouter/auto";      Url = "https://openrouter.ai/settings/keys";         Probe = "https://openrouter.ai/api/v1/key" },
    @{ Id = "openai";     Label = "OpenAI";                            Model = "gpt-4o";               Url = "https://platform.openai.com/api-keys";        Probe = "https://api.openai.com/v1/models" },
    @{ Id = "gemini";     Label = "Google Gemini";                     Model = "gemini-2.0-flash";     Url = "https://aistudio.google.com/app/apikey";      Probe = "https://generativelanguage.googleapis.com/v1beta/openai/models" },
    @{ Id = "mistral";    Label = "Mistral";                           Model = "mistral-large-latest"; Url = "https://console.mistral.ai/api-keys";         Probe = "https://api.mistral.ai/v1/models" },
    @{ Id = "groq";       Label = "Groq";                              Model = "llama-3.3-70b-versatile"; Url = "https://console.groq.com/keys";            Probe = "https://api.groq.com/openai/v1/models" },
    @{ Id = "xai";        Label = "xAI (Grok)";                        Model = "grok-2-latest";        Url = "https://console.x.ai";                        Probe = "https://api.x.ai/v1/models" },
    @{ Id = "deepseek";   Label = "DeepSeek";                          Model = "deepseek-chat";        Url = "https://platform.deepseek.com/api_keys";      Probe = "https://api.deepseek.com/models" },
    @{ Id = "together";   Label = "Together AI";                       Model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"; Url = "https://api.together.ai/settings/api-keys"; Probe = "https://api.together.xyz/v1/models" },
    @{ Id = "local";      Label = "Local (Ollama / LM Studio / OpenAI-compatible)"; Model = ""; Url = ""; Probe = "" }
)

function Test-ProviderKey([hashtable]$Provider, [string]$Key, [string]$BaseUrl = "") {
    # 0 = valid, 1 = rejected, 2 = unknown/unreachable
    $probe = if ($Provider.Id -eq "local") { "$($BaseUrl.TrimEnd('/'))/models" } else { $Provider.Probe }
    if (-not $probe) { return 2 }
    $headers = @{}
    if ($Provider.Id -eq "anthropic") { $headers = @{ "x-api-key" = $Key; "anthropic-version" = "2023-06-01" } }
    elseif ($Provider.Id -ne "local") { $headers = @{ "Authorization" = "Bearer $Key" } }
    try {
        $response = Invoke-WebRequest -Uri $probe -Headers $headers -Method GET -TimeoutSec 12 -UseBasicParsing
        if ($response.StatusCode -eq 200) { return 0 }
        return 1
    }
    catch [System.Net.WebException] {
        if ($_.Exception.Response) { return 1 }
        return 2
    }
    catch { return 2 }
}

function Invoke-OneProvider {
    $script:ConfiguredProvider = $null
    Write-Host ""
    Write-AethOS "Choose an AI provider - you can add more later or from Mission Control."
    for ($i = 0; $i -lt $script:Providers.Count; $i++) {
        Write-Host ("  {0,2}  {1}" -f ($i + 1), $script:Providers[$i].Label)
    }
    Write-Host "   s  Skip for now"
    $choice = Read-AethOSInput "Provider" "1"
    if ($choice -match "^[Ss]") { return $false }
    $index = 0
    if (-not [int]::TryParse($choice, [ref]$index) -or $index -lt 1 -or $index -gt $script:Providers.Count) {
        Write-Warn "Invalid choice: $choice"
        return $false
    }
    $provider = $script:Providers[$index - 1]
    $upper = $provider.Id.ToUpperInvariant()

    if ($provider.Id -eq "local") {
        $base = Read-AethOSInput "OpenAI-compatible base URL" "http://localhost:11434/v1"
        $model = Read-AethOSInput "Model name (as served locally, e.g. llama3.2)" ""
        if ((Test-ProviderKey $provider "" $base) -eq 0) { Write-Ok "Local model server responded at $base" }
        else { Write-Warn "No response from $base - saved anyway; start your local server before .\run.ps1" }
        Set-EnvValue "LOCAL_LLM_BASE_URL" $base
        if ($model) { Set-EnvValue "LOCAL_LLM_MODELS" $model }
        $script:ConfiguredProvider = "local"
        return $true
    }

    if ($provider.Url) { Write-Note "Get a key: $($provider.Url)" }
    $key = Read-AethOSSecret "$($provider.Label) API key"
    if (-not $key) { Write-Warn "No key entered - skipped $($provider.Label)."; return $false }
    Write-AethOS "Validating the key with $($provider.Label) (a free metadata call - no tokens are spent)..."
    $result = Test-ProviderKey $provider $key
    if ($result -eq 0) { Write-Ok "Key verified with $($provider.Label)" }
    elseif ($result -eq 1) {
        Write-Warn "$($provider.Label) rejected this key."
        if (-not (Confirm-AethOS "Save it anyway?" "n")) { return $false }
    }
    else { Write-Warn "Could not reach $($provider.Label) to validate (offline?). Saving unverified." }
    Set-EnvValue "${upper}_API_KEY" $key
    $model = Read-AethOSInput "Default model" $provider.Model
    if ($model) { Set-EnvValue "${upper}_MODEL" $model }
    $script:ConfiguredProvider = $provider.Id
    return $true
}

function Invoke-Setup {
    Write-Section "6 / 6  Setup"
    Assert-Root
    Push-Location $script:Root
    try {
        if ($NoOnboard) {
            Write-Note "Onboarding skipped. Run it any time: .\install.ps1 -Onboard"
            return
        }
        $envPath = Join-Path $script:Root ".env"
        if (-not $Onboard -and (Test-Path $envPath) -and (Select-String -Path $envPath -Pattern "^USE_REAL_LLM=true" -Quiet)) {
            Write-Ok "AI provider already configured in .env - onboarding not needed"
            Write-Note "Reconfigure any time: .\install.ps1 -Onboard"
            return
        }
        if (-not (Test-Interactive)) {
            Write-Warn "No interactive terminal detected - skipping guided setup."
            Write-Note "Finish setup any time: cd `"$($script:Root)`"; .\install.ps1 -Onboard"
            return
        }

        Write-AethOS "Interactive setup - every answer is written to $($script:Root)\.env and stays on this machine."

        if (Confirm-AethOS "Single-user self-host mode (recommended for a personal install)?" "y") {
            Set-EnvValue "SELF_HOST" "true"
            Write-Ok "Self-host mode enabled - no signup wall, you own the instance"
        }

        if (-not (Test-EnvHas "AETHOS_VAULT_KEY")) {
            $venvPython = Join-Path $script:Root ".venv\Scripts\python.exe"
            try {
                $vaultKey = (& $venvPython -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>$null)
                if ($vaultKey) {
                    Set-EnvValue "AETHOS_VAULT_KEY" $vaultKey.Trim()
                    Write-Ok "Generated the credential-vault encryption key"
                }
            }
            catch { Write-Warn "Could not generate a vault key automatically; set AETHOS_VAULT_KEY in .env later." }
        }

        if (Confirm-AethOS "Protect Mission Control with a login passphrase?" "n") {
            $pass = Read-AethOSSecret "Choose a passphrase"
            if ($pass) {
                Set-EnvValue "AETHOS_LOGIN_ENABLED" "true"
                Set-EnvValue "AETHOS_LOGIN_PASSPHRASE" $pass
                Write-Ok "Login passphrase set"
            }
        }

        $firstProvider = $null
        $any = $false
        while ($true) {
            if (Invoke-OneProvider) {
                $any = $true
                if (-not $firstProvider) { $firstProvider = $script:ConfiguredProvider }
                if (-not (Confirm-AethOS "Add another provider?" "n")) { break }
            }
            else { break }
        }
        if ($any) {
            Set-EnvValue "USE_REAL_LLM" "true"
            if ($firstProvider -ne "local") { Set-EnvValue "ACTIVE_PROVIDER" $firstProvider }
            Write-Ok "AI reasoning enabled (ACTIVE_PROVIDER=$firstProvider)"
        }
        else {
            Write-Warn "No AI provider configured - AethOS starts in limited mode."
            Write-Note "Add one later: .\install.ps1 -Onboard, or Mission Control > Connections."
        }

        if (Confirm-AethOS "Enable web research (needs a Tavily API key)?" "n") {
            $searchKey = Read-AethOSSecret "Tavily API key (tvly-...)"
            if ($searchKey) {
                Set-EnvValue "WEB_RESEARCH_ENABLED" "true"
                Set-EnvValue "WEB_SEARCH_PROVIDER" "tavily"
                Set-EnvValue "WEB_SEARCH_API_KEY" $searchKey
                Write-Ok "Web research enabled"
            }
        }

        if (Confirm-AethOS "Connect a Telegram bot?" "n") {
            $tg = Read-AethOSSecret "Telegram bot token (from @BotFather)"
            if ($tg) {
                Set-EnvValue "TELEGRAM_ENABLED" "true"
                Set-EnvValue "TELEGRAM_BOT_TOKEN" $tg
                Write-Ok "Telegram channel enabled"
            }
        }

        Write-Ok "Setup complete - configuration saved to .env"
    }
    finally { Pop-Location }
}

function Test-AethOSRoot([string]$Path) {
    if (-not $Path) { return $false }
    $project = Join-Path $Path "pyproject.toml"
    return (Test-Path $project) -and (Select-String -Path $project -Pattern '^name\s*=\s*"aethos"' -Quiet)
}

function Invoke-Uninstall {
    $target = Find-ExistingRoot
    if (-not $target) { $target = [IO.Path]::GetFullPath($InstallDir) }
    if (-not (Test-AethOSRoot $target)) { Write-Fail "No AethOS install found at $target."; exit 2 }
    Show-Banner
    Write-Warn "This removes the AethOS install at $target (source, venv, dependencies, installer state)."
    $envPath = Join-Path $target ".env"
    if (Test-Path $envPath) {
        $backup = Join-Path $HOME ("aethos-env-backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
        if (Confirm-AethOS "Save a copy of your .env configuration to $backup first?" "y") {
            Copy-Item $envPath $backup
            Write-Ok "Saved $backup"
        }
    }
    if (-not (Confirm-AethOS "Permanently remove $target?" "n")) {
        Write-AethOS "Uninstall cancelled - nothing was removed."
        exit 0
    }
    Set-Location $HOME
    Remove-Item -Recurse -Force $target -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$target.installer" -ErrorAction SilentlyContinue
    Write-Ok "AethOS removed from $target."
    Write-Note "Reinstall any time: irm $($script:InstallerUrl) | iex"
}

function Invoke-ReinstallPrep {
    $target = Find-ExistingRoot
    if (-not $target) { $target = [IO.Path]::GetFullPath($InstallDir) }
    if (-not (Test-AethOSRoot $target)) { Write-Fail "No AethOS install found at $target - run a normal install instead."; exit 2 }
    Write-Warn "Reinstall removes $target and installs the latest version fresh."
    $envPath = Join-Path $target ".env"
    if (Test-Path $envPath) {
        if (Confirm-AethOS "Keep your current .env configuration for the new install?" "y") {
            $script:RestoreEnv = Join-Path ([IO.Path]::GetTempPath()) ("aethos-env-" + [Guid]::NewGuid().ToString("N"))
            Copy-Item $envPath $script:RestoreEnv
            Write-Ok "Your .env will be restored after the reinstall"
        }
    }
    if (-not (Confirm-AethOS "Remove $target and reinstall now?" "n")) {
        Write-AethOS "Reinstall cancelled - nothing was removed."
        exit 0
    }
    Set-Location $HOME
    Remove-Item -Recurse -Force $target -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$target.installer" -ErrorAction SilentlyContinue
    $script:Root = $null
    Initialize-State
    Write-Ok "Old install removed - installing fresh"
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
            "setup" { Invoke-Setup }
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
    $envPath = Join-Path $script:Root ".env"
    if ((Test-Path $envPath) -and (Select-String -Path $envPath -Pattern "^USE_REAL_LLM=true" -Quiet)) {
        $active = (Select-String -Path $envPath -Pattern "^ACTIVE_PROVIDER=(.+)$" | Select-Object -First 1).Matches.Groups[1].Value
        Write-Host "  AI provider       Configured ($active) - manage more in Mission Control > Connections"
    }
    else {
        Write-Host "  AI provider       Not configured yet - run: .\install.ps1 -Onboard"
        Write-Note "Supported: Anthropic / OpenRouter / OpenAI / Gemini / Mistral / Groq / xAI / DeepSeek / Together / local (Ollama, LM Studio)"
    }
    Write-Host ""
    Write-Note "Update:           .\install.ps1 -Update"
    Write-Note "Reinstall fresh:  .\install.ps1 -Reinstall     Uninstall: .\install.ps1 -Uninstall"
    Write-Note "Setup wizard:     .\install.ps1 -Onboard"
    Write-Note "Installer status: .\install.ps1 -Status"
    Write-Note "Step help:        .\install.ps1 -HelpStep STEP"
    Write-Note "Detailed log:     $($script:LogFile)"
    Write-Note "Mutation execution and host shell access are still disabled."
}

if ($Help) { Show-Usage; exit 0 }
if ($HelpStep) { Show-StepHelp $HelpStep; exit 0 }
Initialize-State
if ($Status) { Show-Status; exit 0 }
if ($Uninstall) { Invoke-Uninstall; exit 0 }

# Existing install: offer update / reinstall / onboarding instead of a blind re-run.
if (-not ($Update -or $Reinstall -or $Onboard -or $Resume -or $From)) {
    $existing = Find-ExistingRoot
    if ($existing -and (Test-Path (Join-Path $existing ".venv")) -and (Test-Interactive)) {
        Write-AethOS "AethOS is already installed at $existing."
        Write-Host "  U  Update to the latest version (default)"
        Write-Host "  R  Remove it and reinstall fresh"
        Write-Host "  O  Run only the setup wizard (providers, passphrase)"
        Write-Host "  Q  Quit without changing anything"
        $choice = Read-AethOSInput "What would you like to do?" "U"
        switch -Regex ($choice) {
            "^[Rr]" { $Reinstall = $true }
            "^[Oo]" { $Onboard = $true }
            "^[Qq]" { Write-AethOS "No changes made."; exit 0 }
            default { $Update = $true }
        }
    }
}

try {
    if ($Onboard) {
        $script:Root = Find-ExistingRoot
        if (-not (Test-AethOSRoot $script:Root)) { Write-Fail "No existing install found - run the installer first."; exit 2 }
        Show-Banner
        $script:CurrentStep = "setup"
        Invoke-Setup
        exit 0
    }
    Show-Banner
    if ($Reinstall) { Invoke-ReinstallPrep }
    elseif ($Update) {
        Get-ChildItem -Path $script:StateDir -Filter "*.done" -ErrorAction SilentlyContinue | Remove-Item -Force
        Write-AethOS "Updating AethOS to the latest '$Branch'..."
    }
    Write-Note "Progress is checkpointed; a failed run can continue with -Resume."
    Invoke-Steps
    $script:CurrentStep = "complete"
    Show-Success
    if (-not $NoStart -and (Test-Interactive) -and (Confirm-AethOS "Start AethOS now?" "y")) {
        Write-AethOS "Starting AethOS - press Ctrl+C to stop it."
        Set-Location $script:Root
        if ($SkipWeb) { & (Join-Path $script:Root "run.ps1") -ApiOnly -ApiPort $ApiPort }
        else { & (Join-Path $script:Root "run.ps1") -ApiPort $ApiPort -WebPort $WebPort }
    }
    else {
        Write-Note "Start later: cd `"$($script:Root)`"; .\run.ps1"
    }
}
catch {
    Stop-Install $_
    exit 1
}
