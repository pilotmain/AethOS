<div align="center">

# AethOS

**Governed agentic operating system** for orchestration, evidence, mutations, engineering intelligence, and multi-channel runtime operations.

<br />

<!-- Primary identity -->
<p>
  <img src="https://img.shields.io/badge/Governed_Agentic_OS-0891b2?style=flat-square&labelColor=0f172a&color=164e63" alt="Governed Agentic OS" />
  <img src="https://img.shields.io/badge/Operational_Intelligence_Platform-1e293b?style=flat-square&labelColor=0f172a&color=334155" alt="Operational Intelligence Platform" />
  <img src="https://img.shields.io/badge/Mission_Control_Runtime-059669?style=flat-square&labelColor=0f172a&color=047857" alt="Mission Control Runtime" />
</p>

<!-- Secondary specs -->
<p>
  <img src="https://img.shields.io/badge/License-Apache_2.0-0891b2?style=flat-square&labelColor=0f172a" alt="Apache 2.0" />
  <img src="https://img.shields.io/badge/Contributions-Welcome-475569?style=flat-square&labelColor=0f172a&color=64748b" alt="Contributions welcome" />
  <img src="https://img.shields.io/badge/Python-3.11+-059669?style=flat-square&labelColor=0f172a" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Mutation_Governance-cyan?style=flat-square&labelColor=0f172a&color=0891b2" alt="Mutation Governance" />
  <img src="https://img.shields.io/badge/Browser_Evidence_Engine-0891b2?style=flat-square&labelColor=0f172a&color=0e7490" alt="Browser Evidence Engine" />
</p>

<br />

*AethOS separates orchestration from execution through policy, evidence, verification, approval, and audit.*

<br />

[**Install**](#install-aethos) · [**Architecture**](#architecture) · [**Mission Control**](#mission-control) · [**Contribute**](CONTRIBUTING.md) · [**Docs**](docs/README.md)

</div>

---

## What is AethOS?

AethOS is a **secure operational intelligence platform** — not a chatbot wrapper and not an unrestricted shell.

It routes every operational action through a governed lifecycle:

```text
Channels → Orchestration → Policy → Provider Runtime → Evidence → Verification → Mission Control → Audit
```

**Why it matters:** multi-channel intents (chat, Telegram, Mission Control) converge on one orchestration brain with readonly-first analysis, explicit approval for mutations, and auditable artifacts.

**Why trust it:** no hidden automation · no auto-merge · no silent background coding · evidence before action.

---

## Install AethOS

*Operational orchestration runtime for governed AI systems.*

macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | iex
```

Windows with `curl.exe`:

```powershell
curl.exe -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | powershell.exe -NoProfile -ExecutionPolicy Bypass -Command -
```

The installer is idempotent and checkpoints every stage. If a network,
dependency, or verification step stops, fix the reported cause and continue:

```bash
./install.sh --resume                 # macOS / Linux
```

```powershell
.\install.ps1 -Resume                 # Windows
```

Every stage has focused help (`./install.sh --help-step preflight` or
`.\install.ps1 -HelpStep preflight`) and a status view (`--status` / `-Status`).
See the [complete installation guide](docs/INSTALL.md) for prerequisites,
custom paths, API-only installs, recovery, and upgrades.

Or install from a local clone:

```bash
git clone https://github.com/pilotmain/AethOS.git
cd AethOS
./install.sh
```

The installer will:

- Preserve a local checkout or clone into `~/aethos` (override with `AETHOS_INSTALL_DIR`)
- Checkpoint preflight, source, backend, frontend, and verification stages
- Install the Mission Control API runtime (FastAPI · port `8010`)
- Configure the local orchestration environment (`.env` from template)
- Install cloud adapters and secure local-vault support
- Set up the Mission Control web UI (Next.js · port `3000`)
- **Leave mutation execution disabled by default** — enable explicitly in `.env`
- Verify the API, CLI, and frontend toolchain before reporting success
- Print the **first-run URL**, doctor command, recovery command, and log path

Then launch:

```bash
./run.sh
```

On Windows use `.\run.ps1`. Both launchers support `--help` / `-Help` and
API-only or web-only modes.

Open the first-run URL below. You'll sign in (if a login passphrase is set),
then a short first-run setup learns your name, working hours, timezone, and
preferred tone so AethOS can address you naturally.

| Surface | URL |
|---------|-----|
| First-run / Mission Control UI | http://localhost:3000 |
| Mission Control API | http://127.0.0.1:8010 |
| Health | http://127.0.0.1:8010/api/v1/health |

---

## Architecture

AethOS uses a **model-as-brain** pattern: the Mission Control provider (Anthropic, OpenRouter, local LLM, etc.) routes and answers; AethOS exposes tools, executes governed operations, and enforces policy. Capabilities are **provider-agnostic** — generic over the MC provider registry and per-tenant credential vault, not hardcoded to any single cloud.

```text
        Channels (Web · Telegram · API)
                    │
                    ▼
         Single-loop orchestration
    (model tool loop · readonly-first routing)
                    │
                    ▼
         Policy + Governance Layer
      (approval · blast radius · blocks)
                    │
                    ▼
     Provider runtime (registry + vault)
    Railway · GitHub · Vercel · AWS · …
                    │
                    ▼
      Evidence + Verification Engine
   (browser capture · artifacts · tests)
                    │
                    ▼
              Mission Control
        (observability · audit · engineering)
```

**Reads run directly.** Mutations route through preflight → human approval → the correct provider tool.

---

## Verified capabilities

These are the capabilities verified by `pytest tests -q -k beta_smoke` and advertised in onboarding:

- One model-driven chat loop with governed mutation gates — questions never become deploy targets
- Summarize URLs and follow up from conversation memory without canned help blurbs
- Render structured operational views to the live Canvas panel
- Send Telegram messages with real transport errors surfaced (no generic failure literals)
- Diagnose channel health (Telegram webhook, tokens) before workspace or repo commands
- Run Railway read-only deployment and inventory checks directly — no preflight job
- List provider inventory with live health tables across every connected cloud
- Analyze connected GitHub repositories via API — no local workspace registration required
- Run multi-model arbiter consensus when at least two models are configured
- Check deploy readiness directly; route deploy mutations through approval with the right provider tool
- Review connected repo structure, dependencies, and CI workflows via GitHub API

Multi-tenant isolation and mutation governance apply to every capability above.

---

## Mission Control

Mission Control is the operational surface — designed for **orchestration clarity**, not chat aesthetics.

- Sidebar navigation: Runtime · Providers · Browser · **Engineering** · System
- Provider cards with collapsed credential management
- Mutation audit trail and operation preflights
- Engineering workspace cards, architecture maps, dependency health

Open after `./run.sh`: **http://localhost:3000/mission-control**

---

## Governance guarantees

| Guarantee | Status |
|-----------|--------|
| Readonly-first engineering analysis | Enforced |
| Mutation preflight before writes | Enforced |
| Human approval for governed execution | Required |
| Browser capture policy tiers | Enforced |
| Audit artifacts for evidence operations | Generated |
| Unrestricted shell / auto-merge | **Blocked** |

---

## Quick start (manual)

```bash
git clone https://github.com/pilotmain/AethOS.git
cd AethOS
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn aethos_core.api.main:app --reload --port 8010
```

```bash
cd web
echo 'NEXT_PUBLIC_API_BASE=http://127.0.0.1:8010' > .env.local
npm install && npm run dev
```

See [docs/SETUP.md](docs/SETUP.md) for provider keys, browser automation, and Telegram.

---

## Documentation

| Doc | Topic |
|-----|-------|
| [Documentation index](docs/README.md) | Supported user, operator, and developer guides |
| [Installation](docs/INSTALL.md) | One-command install, resume, Windows, upgrades |
| [Setup](docs/SETUP.md) | Full install and environment |
| [Brand & install experience](docs/BRAND_AND_INSTALL_EXPERIENCE.md) | Visual identity, terminology, onboarding |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Runtime](docs/RUNTIME.md) | Chat lanes, jobs, orchestration |
| [Testing](docs/TESTING.md) | Test strategy |

---

## Development

```bash
pytest tests/ -q
cd web && npm test -- --run
```

Reliability gate: `pytest tests/test_chat_20_turn.py -q`

Before opening a pull request, read [CONTRIBUTING.md](CONTRIBUTING.md). All
contributions require review, passing checks, and a DCO sign-off. Project roles
and decisions are described in [GOVERNANCE.md](GOVERNANCE.md).

---

## License

AethOS is open source under the [Apache License 2.0](LICENSE). See
[LICENSING.md](LICENSING.md) and [COPYRIGHT.md](COPYRIGHT.md) for scope,
attribution, and contributor ownership.

---

<div align="center">

**AethOS** — confidence at first command.

</div>
