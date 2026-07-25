# Plugin SDK

## Package

`aethos_sdk/` — governed extensibility framework.

## Plugin types

| Type | Purpose |
|------|---------|
| provider_adapter | New platforms (Railway, custom CI) |
| intelligence_module | Custom analyzers |
| channel_adapter | Slack, Discord, etc. |
| operational_rule | Custom governance rules |
| evidence_processor | Enterprise telemetry ingestion |

## Governance (mandatory)

Plugins **cannot**:
- Bypass approval
- Mutate without orchestration
- Access secrets directly
- Execute unrestricted shell

All plugins run sandboxed with `approval_required: true`.

## Register a plugin

```python
from aethos_sdk.plugin_types import PluginManifest
from aethos_sdk.plugin_registry import register_plugin

register_plugin(PluginManifest(
    plugin_id="my-adapter",
    name="My Provider Adapter",
    plugin_type="provider_adapter",
    version="1.0.0",
    sandboxed=True,
))
```

## API

```bash
GET  /api/v1/plugins
POST /api/v1/plugins/enable
```

Mission Control → Production Infrastructure → Plugin Center
