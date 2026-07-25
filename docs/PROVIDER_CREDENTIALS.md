# Provider Credentials

## Supported providers

- **Anthropic** — LLM reasoning (`USE_REAL_LLM`, `ANTHROPIC_API_KEY`)
- **GitHub** — workflow/CI readonly probes
- **Railway** — deployment diagnostics
- **Vercel** — deployment diagnostics
- **Tavily** — web research (see [RESEARCH_SETUP.md](RESEARCH_SETUP.md))

## Storage

Credentials are stored in the governed vault under `data/credentials` with encryption via the `cryptography` package.

Never commit secrets. `.env` is gitignored.

## Mission Control

**Credential Center** — add, rotate, and revalidate credentials  
**Provider Inventory** — connection status rollup

## Environment variables (LLM)

```env
USE_REAL_LLM=true
ACTIVE_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Restart API after changes.

## Validation

```bash
aethos doctor --category providers
```

Or Mission Control → Enterprise Readiness → Environment Doctor

## Safe defaults

Provider credentials are optional for deterministic/local mode. AethOS operates without LLM keys using governed deterministic lanes.
