# Runtime

## Authority (`aethos_core/runtime/authority.py`)

Single process-level snapshot:

| Field | Meaning |
|-------|---------|
| `transport` | API reachability |
| `auth` | Token validity (dev: open) |
| `panel` | Observational MC state — **does not block chat** |
| `chat_ready` | Send allowed when transport OK and auth not invalid |
| `provider_available` | Real LLM configured |

## Chat lanes

### Lane A — Deterministic

Detected by `aethos_core/chat/lanes.py`. Handlers in `handlers.py`.

Returns immediately. No provider. Used for capabilities, Vercel, terminal, config, setup, runtime status.

### Lane B — Provider

`aethos_core/provider/completion.py` — sync Anthropic when configured; template fallback otherwise.

Entry: `POST /api/v1/chat` → `resolve_chat_turn()`.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Runtime + chat readiness |
| POST | `/api/v1/chat` | Unified chat (A then B) |
| POST | `/api/v1/chat/deterministic` | Lane A only (422 if generative) |

## Config (`aethos_core/config.py`)

Loaded once via `get_settings()`. Environment variables in `.env.example`.
