# Kubernetes Setup

## Helm chart

Chart location: `deploy/helm/aethos/`

```bash
helm install aethos deploy/helm/aethos \
  --set deploymentMode=team \
  --set workerMode=standalone \
  --set ingress.enabled=true \
  --set ingress.host=aethos.example.com
```

## Components

| Resource | Purpose |
|----------|---------|
| Deployment (api) | FastAPI orchestration |
| Deployment (worker) | Isolated worker containers |
| Service | API port 8010 |
| ConfigMap | Non-secret env (DEPLOYMENT_MODE, WORKER_MODE) |
| PVC | Artifact persistence (10Gi default) |
| Ingress | Optional external access |

## Health probes

- **Liveness:** `/api/v1/health`
- **Readiness:** `/api/v1/enterprise/health`

## Rolling deploys

API deployment uses `RollingUpdate` with `maxUnavailable: 0`.

## Autoscaling

Enable in `values.yaml`:

```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 3
```

## Secrets

Store sensitive values (WEB_API_TOKEN, provider keys) in Kubernetes Secrets — never ConfigMaps.

Mount credentials via envFrom secretRef in production overlays.
