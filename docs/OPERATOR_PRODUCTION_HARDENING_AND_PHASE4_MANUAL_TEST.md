# Operator production hardening + Phase 4 manual test

**Purpose:** Validate doctor profiles (break-glass + ngrok) and cloud readonly inventory probes before continuing development.

**Prerequisites:** API on `:8010`, `.env` pulled, `git pull` latest.

---

## Environment setup

Add or confirm in `.env`:

```bash
# Shared operator session (default)
export SID=operator

# Doctor: relaxed break-glass in local dev (pick one ack path)
AETHOS_OPERATOR_BREAK_GLASS_ACKNOWLEDGED=true
# — or —
AETHOS_LOCAL_ENV_TRUSTED=true

# Optional explicit profile (default infers from OPERATIONAL_ENVIRONMENT)
AETHOS_DOCTOR_PROFILE=development

# Phase 4 cloud probes
CLOUD_READONLY_INVENTORY_ENABLED=true

# Telegram tunnel (only if you use Telegram webhooks)
TELEGRAM_TUNNEL_ENABLED=true
NGROK_AUTHTOKEN=your-token
```

Restart gateway after `.env` changes:

```bash
aethos gateway --reload   # or restart existing uvicorn
```

---

## Block A — Doctor production hardening

### A1. Baseline doctor

```bash
aethos doctor
```

**Pass criteria (development profile + break-glass ack):**

| Check | Expected |
|-------|----------|
| `safe_defaults` | **WARNING** (break-glass listed) or **PASS** — not **FAIL** |
| `ngrok_tunnel` | **WARNING** if tunnel enabled but stopped; **PASS** if running or disabled |
| `cloud_readonly_inventory` | **PASS** or **WARNING** when `CLOUD_READONLY_INVENTORY_ENABLED=true` |
| Overall | **WARNING** or **PASS** — not **FAIL** |

JSON:

```bash
aethos doctor --json | jq '{overall, summary, checks: [.checks[] | {name, status, detail}]}'
```

### A2. Start ngrok tunnel (if Telegram enabled)

```bash
aethos tunnel start
aethos tunnel status
aethos doctor --category tunnel
```

**Pass:** `ngrok_tunnel: PASS` with public URL.

Alternative:

```bash
curl -s -X POST localhost:8010/api/v1/runtime/tunnel/start | jq .
```

### A3. Strict profile spot-check (optional)

Temporarily in shell (do not commit):

```bash
export AETHOS_DOCTOR_PROFILE=strict
# restart API or clear settings cache in new process
aethos doctor --category security
```

**Expected:** `safe_defaults: FAIL` until break-glass flags are disabled.

Restore:

```bash
unset AETHOS_DOCTOR_PROFILE
export AETHOS_DOCTOR_PROFILE=development
```

---

## Block B — Phase 4 cloud readonly probes

### B1. Aggregate inventory API

```bash
curl -s localhost:8010/api/v1/runtime/cloud/inventory | jq '{ok, summary, providers: [.providers[] | {provider, ok, error}]}'
```

**Pass:** `enabled: true`, at least one provider `ok: true` **or** graceful `error` for missing creds (kubectl/gcloud/az/boto3).

### B2. Per-provider probes

```bash
for p in aws gcp azure kubernetes cloudflare; do
  echo "=== $p ==="
  curl -s "localhost:8010/api/v1/runtime/cloud/inventory/$p" | jq '{provider, ok, error}'
done
```

| Provider | Typical local outcome |
|----------|----------------------|
| **kubernetes** | `ok: false`, kubectl not found — acceptable |
| **aws** | `ok: false` without boto3/creds — acceptable |
| **gcp** | `ok: false` without gcloud — acceptable |
| **azure** | `ok: false` without `az` — acceptable |
| **cloudflare** | `ok: true` if `CLOUDFLARE_API_TOKEN` set |

### B3. Doctor cloud check

```bash
aethos doctor --category cloud
```

**Pass:** `cloud_readonly_inventory` documents probe counts.

---

## Block C — Operator continuity regression (quick)

```bash
export SID=operator
aethos message send --session-id "$SID" "show Railway projects"
python -m aethos_core.cli.main operational --session-id "$SID" "what about api?"
curl -s localhost:8010/api/v1/runtime/sessions/$SID/meta | jq '{last_provider, last_subject_label, continue_hint}'
```

**Pass:** non-empty `last_subject_label`, follow-up succeeds.

---

## Block D — MCP + live bus (regression)

```bash
curl -s -X POST localhost:8010/api/v1/runtime/mcp/invoke \
  -H 'Content-Type: application/json' \
  -d '{"name":"aethos_health","arguments":{}}' | jq '.ok'

curl -s -X POST localhost:8010/api/v1/mission-control/live/publish \
  -H 'Content-Type: application/json' \
  -d '{"type":"manual_test","payload":{"gate":"phase4"}}' | jq '.ok'
```

---

## Sign-off checklist

| Gate | Pass |
|------|------|
| Doctor overall not FAIL in dev with break-glass ack | ☐ |
| Tunnel start via `aethos tunnel start` (if Telegram) | ☐ |
| Cloud inventory API returns probe matrix | ☐ |
| Session meta labels populated | ☐ |
| MCP + live bus smoke | ☐ |

When all checked: **production hardening + Phase 4 manual gate complete** — safe to continue feature development.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `safe_defaults: FAIL` | Set `AETHOS_OPERATOR_BREAK_GLASS_ACKNOWLEDGED=true` or `AETHOS_LOCAL_ENV_TRUSTED=true`; or use `AETHOS_DOCTOR_PROFILE=development` |
| `ngrok_tunnel: FAIL` in dev | Run `aethos tunnel start` or set `TELEGRAM_TUNNEL_ENABLED=false` |
| Cloud inventory disabled | `CLOUD_READONLY_INVENTORY_ENABLED=true` + restart API |
| Railway rate limit on inventory | Cached fallback applies — see `KERNEL_USER_FRICTION_REPORT.md` |
