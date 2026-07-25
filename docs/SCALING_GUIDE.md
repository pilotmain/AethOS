# Scaling Guide

## Worker scaling

Set `WORKER_MODE=standalone` and run additional worker containers:

```bash
aethos worker --worker-id worker-2
```

Docker Compose includes isolated `worker` service. Kubernetes Helm chart supports `workerReplicaCount`.

## Queue backends

| Mode | Backend |
|------|---------|
| local / embedded | in_memory |
| team / enterprise | durable_file (crash recovery) |

Queue API: visible in `GET /api/v1/production/cluster`.

## Distributed schedulers

Scheduler cycles acquire leases to prevent duplicate execution:

```python
from aethos_core.runtime.distributed.distributed_scheduler import run_distributed_cycle
```

Only one worker runs a given cycle at a time.

## Scaling domains

Independent scaling targets:
- research runtime
- browser runtime
- engineering validation
- replay reconstruction
- provider polling
- operational intelligence
- presence cycles

## Backpressure

When browser worker overload detected, queue depth increases — monitor via observability metrics.

## HA readiness

`enterprise` and `hosted` deployment modes enable HA topology flags. Full Redis/Postgres queue backend deferred to future release.

## Metering

Usage tracked per org for capacity planning:

```bash
GET /api/v1/observability/metering
```

Dimensions: runtime minutes, browser captures, research requests, engineering executions, storage.
