# SPDX-License-Identifier: Apache-2.0
"""Operator gateway and CLI — terminal-first workflow."""

# Operator CLI and gateway

Run the API as a local gateway, then drive chat from the terminal.

## Quick start

```bash
aethos onboard
aethos doctor

# Terminal 1 — gateway
aethos gateway --reload

# Terminal 2 — status and chat
aethos status
aethos message send "show Railway projects"

# Operational CLI (session-scoped; default session is `operator`)
export AETHOS_SESSION_ID=operator
python -m aethos_core.cli.main operational --session-id "$AETHOS_SESSION_ID" "show vercel projects"
python -m aethos_core.cli.main operational --session-id "$AETHOS_SESSION_ID" "what about api?"
```

## Commands

| Command | Purpose |
|---------|---------|
| `aethos onboard` | First-run checklist |
| `aethos gateway` | Start uvicorn API on `:8010` |
| `aethos status` | Runtime + provider snapshot |
| `aethos logs` | Tail recent gateway logs |
| `aethos tunnel start` | Start ngrok tunnel for Telegram webhooks |
| `aethos message send "..."` | POST chat through gateway |

## Environment

Set `OPERATIONAL_ENVIRONMENT=development|staging|production` so external channels (Slack, SMS, Telegram) stamp replies with the correct environment banner.

## Slack E2E

1. Set `SLACK_ENABLED=true`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`.
2. Point Slack Events API to `POST /api/v1/slack/events`.
3. Messages route through the same `resolve_chat_turn` brain as web chat.

## Feature flags

Review `.env.example` and the Mission Control configuration view before enabling
autonomous execution, external channels, browser automation, or provider
mutations. Keep mutation features disabled until the corresponding credentials,
approval flow, and recovery procedure have been tested.
