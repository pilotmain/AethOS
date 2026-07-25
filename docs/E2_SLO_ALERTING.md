# §E2 SLO panel & alerting hooks

Mission Control **Observability** renders live SLO rows from `GET /api/v1/observability/slo` (`evaluate_slos()`).

## Targets (defaults in `config.py`)

| Signal | Default target | Metric key |
|--------|----------------|------------|
| Chat turn latency (avg) | ≤ 3000 ms (`SLO_CHAT_LATENCY_MS`) | `chat.latency_ms` histogram |
| Mutation success rate | ≥ 0.95 (`SLO_MUTATION_SUCCESS_RATE`) | `mutation.execute.success` / `mutation.execute.total` |

Warm first paint (&lt; 2s) and job-progress event latency (&lt; 1s) are tracked client-side via Mission Control shell timing and job event streams; extend `evaluate_slos()` when those histograms are exported server-side.

## Alerting hooks

1. **OTEL** — set `OTEL_ENABLED=true` and point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector; SLO breaches appear as metric deltas on the same counters above.
2. **Error sink** — `configure_telemetry()` wires optional Sentry/Datadog when env vars are set (`telemetry_status()` documents active sinks).
3. **CI / cron** — poll `/api/v1/observability/slo` and alert when `ok` is false or `alerts` is non-empty.
4. **Prometheus** — scrape `/api/v1/observability/metrics/prometheus` and alert on `mutation.execute` ratio and chat latency histograms.

## Job trace & replay

- Route trace: `GET /api/v1/observability/route-trace/{session_id}` (last governed chat route metadata).
- Mutation job: `GET /api/v1/observability/job-trace/{job_id}` (truth + audit bundle with `deep_link` for Mission Control).
