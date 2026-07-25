---
name: check-logs
description: Fetch and summarize recent logs for a service from the right provider.
---

## When to use

The operator asks for logs ("show the last 20 logs", "give me top logs for both",
"tail aethos-ui").

## Steps

1. Resolve provider + target from the prompt or active context. Quantifiers like
   "both"/"them"/"those" mean the entities from the previous turn (e.g. both
   Railway services) — never a literal project name.
2. If the operator named a provider explicitly, use it. If there is no provider
   and no context, ask which provider/target.
3. Fetch the requested number of recent log lines (default a small N) for each
   resolved target.
4. Summarize: surface errors/warnings first, include timestamps, and note if logs
   are stale relative to the last deploy/restart.

## Readonly tools

- provider_logs
- recall_last_deployment_thread

## Governance

Read-only. Redact any secrets that appear in log lines.
