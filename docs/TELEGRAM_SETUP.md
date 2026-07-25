# Telegram Setup

## Overview

Telegram is optional. When disabled, AethOS runs in web-only mode (safe default).

## Enable Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Add to `.env`:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token
```

3. Restart the API
4. Verify: `aethos doctor --category telegram`

## Webhook vs polling

Production use requires a public webhook URL. For local development, use the ngrok tunnel.

## Tunnel (ngrok)

```env
TELEGRAM_TUNNEL_ENABLED=true
NGROK_AUTHTOKEN=your-ngrok-token
NGROK_TARGET_PORT=8010
```

Mission Control → Runtime Tunnel → Start tunnel

Doctor check: `aethos doctor --category tunnel`

## Credential vault (recommended)

Store the bot token in Mission Control → Credential Center instead of plain `.env` when possible.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Token missing | `TELEGRAM_BOT_TOKEN` or vault credential |
| Webhook not set | Tunnel running; public URL reachable |
| Messages not delivered | `GET /api/v1/channels/telegram/status` |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
