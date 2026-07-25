# Troubleshooting

## First step

Always run:

```bash
aethos doctor
```

Mission Control → Enterprise Readiness → Environment Doctor

Each failing check includes: what failed, likely cause, what to check, next command, and doc link.

## Installer stopped

The installer retains a marker after each completed stage and prints its log
path on failure. Correct the reported prerequisite or command, then continue:

```bash
./install.sh --resume
./install.sh --status
./install.sh --help-step backend
```

```powershell
.\install.ps1 -Resume
.\install.ps1 -Status
.\install.ps1 -HelpStep backend
```

Use `--from STEP` or `-From STEP` to deliberately re-run a stage and all later
stages. The installer never overwrites `.env`, `web/.env.local`, credentials,
or a checkout containing local changes.

## Common issues

### API not reachable

- **Cause:** uvicorn not running or wrong port
- **Fix:** `./run.sh` or check `API_PORT` in `.env`
- **Details:** docs/LOCAL_DEVELOPMENT.md

### Web UI not loading

- **Cause:** Next.js dev server not running
- **Fix:** `cd web && npm run dev`
- **Check:** `NEXT_PUBLIC_API_BASE` in `web/.env.local`

### Telegram token missing

- **Cause:** `TELEGRAM_ENABLED=true` without token
- **Fix:** Add token or disable Telegram
- **Details:** docs/TELEGRAM_SETUP.md

### Research misconfigured

- **Cause:** `WEB_RESEARCH_ENABLED=true` without Tavily key
- **Fix:** Configure provider or disable research
- **Details:** docs/RESEARCH_SETUP.md

### Browser not ready

- **Cause:** Playwright/Chromium not installed
- **Fix:** `pip install playwright && playwright install chromium`
- **Check:** `aethos doctor --probe-browser`

### Vault unhealthy

- **Cause:** `cryptography` missing or permissions on `data/credentials`
- **Fix:** `pip install cryptography`; check directory permissions

### Unsafe defaults

- **Cause:** `HOST_EXECUTOR_ENABLED=true` or T3 production mutations
- **Fix:** Review `.env`; see Configuration Center
- **Check:** `GET /api/v1/enterprise/safe-defaults`

## Actionable error format

All enterprise diagnostics use structured errors:

- `what_failed`
- `likely_cause`
- `what_to_check`
- `next_command`
- `where_for_details`

## Getting help

1. Export doctor JSON: `aethos doctor --json > doctor.json`
2. Check Mission Control → Operational Health
3. Review audit logs in Mission Control → Audit Logs
