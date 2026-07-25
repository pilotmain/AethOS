# Setup

## One-line install

macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash
cd ~/aethos && ./run.sh
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | iex
cd ~/aethos; .\run.ps1
```

Or install from a clone with `./install.sh` on macOS/Linux or
`.\install.ps1` on Windows. See [INSTALL.md](INSTALL.md) for resume, help,
status, API-only installation, and upgrade controls.

## Prerequisites

- Python 3.11+
- Node.js 20+ (Node.js 24 LTS recommended)
- Git
- 1 GB available disk
- Optional: Vercel CLI (`vercel`) for deployment capability checks

## Backend

```bash
cd AethOS
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn aethos_core.api.main:app --reload --host 0.0.0.0 --port 8010
```

## Frontend

```bash
cd web
echo 'NEXT_PUBLIC_API_BASE=http://127.0.0.1:8010' > .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Provider (optional)

In `.env`:

```env
USE_REAL_LLM=true
ACTIVE_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-api-key>
ANTHROPIC_MODEL=<supported-model-id>
```

Restart the API after changing `.env`.

## Reference codebase

Use a fresh clone or a versioned release as the source of truth. Do not copy
runtime state or credentials from another installation.
