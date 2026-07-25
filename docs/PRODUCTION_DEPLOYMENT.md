# Production Deployment

## Deployment modes

| Mode | Purpose | Topology |
|------|---------|----------|
| `local` | Developer single-node | API + embedded workers |
| `team` | Shared internal server | API + standalone worker + web |
| `enterprise` | Distributed HA | Multi-replica API/workers, durable queue |
| `edge` | Offline operational node | Local vault, delayed sync |
| `hosted` | Managed cloud platform | Tenant-separated hosted MC |

Set in `.env`:

```env
DEPLOYMENT_MODE=team
WORKER_MODE=standalone
APP_ENV=production
```

## Docker (team server)

```bash
docker compose -f docker-compose.prod.yml up -d
```

Services:
- **api** — FastAPI on port 8010
- **worker** — isolated job/scheduler process
- **web** — Mission Control on port 3000

Persistent volume: `aethos_data` → `/app/data`

Health probes:
- API: `GET /api/v1/health`
- Enterprise: `GET /api/v1/enterprise/health`

## CLI

```bash
aethos doctor
aethos worker          # standalone worker process
python -m aethos_core.runtime.worker_main
```

## Production validation

```bash
curl http://localhost:8010/api/v1/production/validate
```

## Runtime topology

```
operators → channels → orchestration authority → governed runtimes
         → distributed execution → observability → adaptive governance
```

Components: web, api, workers, scheduler, browser runtime, artifact storage, vault, queue, observability.

See [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) for Helm deployment.
