# Local Development

## Prerequisites

- Python 3.11+
- Node.js 24 LTS
- Optional: Playwright (`pip install ".[browser]" && playwright install chromium`)
- Optional: ngrok authtoken for Telegram tunnel

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn aethos_core.api.main:app --reload --host 0.0.0.0 --port 8010
```

API docs: http://127.0.0.1:8010/docs

## Frontend

```bash
cd web
echo 'NEXT_PUBLIC_API_BASE=http://127.0.0.1:8010' > .env.local
npm install
npm run dev
```

Mission Control: http://localhost:3000

## CLI

After `pip install -e ".[dev]"`:

```bash
aethos doctor          # environment readiness
aethos doctor --json   # machine-readable output
aethos config          # configuration summary (no secrets)
aethos demo enable     # synthetic demo data
```

## Workspace registration

Local workspace intelligence uses paths under `data/local_workspace`. Register repos via Mission Control → Engineering → Local Workspaces.

Set `AETHOS_WORKSPACE_ROOT` if running from a non-canonical path.

## Running tests

```bash
pytest tests/ -q
pytest tests/test_phase_98j_operational_reliability.py -q
pytest tests/test_phase_98k_enterprise_readiness.py -q
```

## Restart after .env changes

Always restart the API (and web dev server for `NEXT_PUBLIC_*` vars) after editing `.env`.
