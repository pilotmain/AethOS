# Getting Started with AethOS

AethOS is a governed agentic operating system for operational engineering — chat-first, evidence-backed, never self-authorizing.

## Quick start

### macOS or Linux

```bash
curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash
cd ~/aethos && ./run.sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | iex
cd ~/aethos; .\run.ps1
```

Open Mission Control at http://localhost:3000

The install is checkpointed. If it stops, the error shows the exact recovery
command and log path. Resume from completed work with `./install.sh --resume`
or `.\install.ps1 -Resume`. See [Installation](INSTALL.md) for all controls.

## Prerequisites

### macOS prerequisites

- Git
- Python 3.11 or newer
- Node.js 20 or newer; Node.js 24 LTS is recommended
- 1 GB free disk space

With Homebrew: `brew install git python@3.12 node@24`.

### Linux prerequisites

Install Git, Python 3.11+, Node.js 20+ and npm with your distribution package
manager, pyenv, or nvm. Node.js 24 LTS is recommended. AethOS never invokes
`sudo` or silently changes system packages.

### Windows prerequisites

- Git for Windows
- Python 3.11 or newer (the `py` launcher is supported)
- Node.js 20 or newer with npm; Node.js 24 LTS is recommended
- Windows PowerShell 5.1+ or PowerShell 7+

With winget: `winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS`.
Open a new PowerShell window after installing prerequisites.

Run environment checks:

```bash
.venv/bin/aethos doctor
```

On Windows: `.\.venv\Scripts\aethos.exe doctor`.

## First-run checklist

1. **Environment Doctor** — Mission Control → Enterprise Readiness → Environment Doctor (or `aethos doctor`)
2. **Setup Wizard** — Mission Control → Setup Wizard
3. **Configuration Center** — review enabled/disabled features (no secrets shown)
4. **Demo Mode** — enable synthetic data to explore without credentials
5. **Operational Health** — confirm API, scheduler, and reliability scores

## Safe defaults

By default AethOS keeps high-risk capabilities off:

| Feature | Default |
|---------|---------|
| Mutation execution | Off |
| Production mutations (T3) | Off |
| Browser automation | Off |
| Web research | Off |
| Telegram tunnel | Off |
| Host executor (shell) | Off |

Enable features explicitly in `.env` and restart the API after changes.

## Core workflows

- **Chat / Telegram** — ask operational questions; AethOS routes to presence, research, or engineering lanes
- **Mission Control** — observability, preflights, engineering execution, operational trust
- **Governed mutations** — sandbox → validation → PR draft; human approval required

## Documentation index

- [Local Development](LOCAL_DEVELOPMENT.md)
- [Telegram Setup](TELEGRAM_SETUP.md)
- [Provider Credentials](PROVIDER_CREDENTIALS.md)
- [Research Setup](RESEARCH_SETUP.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Demo Script](DEMO_SCRIPT.md)
- [Regression Checklist](REGRESSION_CHECKLIST.md)

## Governance principle

Observe, correlate, prioritize, recommend, prepare, audit — never overwhelm, never spam, never self-authorize.
