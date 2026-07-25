# Research Setup

## Enable web research

```env
WEB_RESEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=tavily
WEB_SEARCH_API_KEY=tvly-...
RESEARCH_ARTIFACTS_DIR=data/research_artifacts
```

Restart the API after editing `.env`.

## Verify

```bash
aethos doctor --category research
```

Mission Control → Research Config

## Usage

Ask research questions via Telegram or Mission Control chat. Artifacts appear in Research Intelligence views.

## Safe default

`WEB_RESEARCH_ENABLED=false` — research is off until explicitly configured.

## Troubleshooting

| Error | Fix |
|-------|-----|
| Provider missing | Set `WEB_SEARCH_PROVIDER=tavily` |
| API key missing | Set `WEB_SEARCH_API_KEY` |
| Research enabled but errors | Check Configuration Center for `research_errors` |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
