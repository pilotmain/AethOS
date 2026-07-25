# Observability

## Metrics

| Metric | Purpose |
|--------|---------|
| orchestration.latency | Runtime health |
| approval.latency | Governance health |
| replay.integrity | Operational trust |
| browser.reliability | Evidence quality |
| provider.stability | Operational risk |
| signal.quality | Fatigue prevention |
| execution.reliability | Mutation trust |
| research.confidence | Evidence quality |

## Endpoints

```bash
GET /api/v1/observability/dashboard
GET /api/v1/observability/metrics
GET /api/v1/observability/metrics/prometheus
GET /api/v1/observability/metering
```

## Prometheus

Scrape target: `/api/v1/observability/metrics/prometheus`

## Integrations (ready)

- OpenTelemetry — structured trace hooks
- Prometheus + Grafana — metrics scraping
- Loki — log shipping from audit JSONL
- Splunk / DataDog — via Prometheus remote write

## Mission Control

Production Infrastructure → Observability
