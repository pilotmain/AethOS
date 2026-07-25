# Railway staging / production — shared store requirements

Canvas, workspace documents, notes/tasks, and session-alias state must use a **shared backing store** when `DEPLOYMENT_MODE=hosted`. Process-local JSON files under `data/` are not visible across:

- API vs worker containers (durable agent jobs)
- Multiple API replicas behind the load balancer

## Postgres (required for canvas on hosted)

1. **Provision Postgres** (Railway Postgres plugin) and set `DATABASE_URL` on every service that runs AethOS Python code.

2. **Set `AETHOS_VAULT_KEY`** (secret, identical on api and any worker) so encrypted credentials in Postgres decrypt on every process. Without it, api and worker each generate a local machine key and cannot read each other's vault writes.

```bash
railway variable set --service aethos-api AETHOS_VAULT_KEY='…long-random-secret…'
```

3. **Canvas** (`canvas_views` table) and **credential vault** persist to Postgres when `DATABASE_URL` is set.

```bash
railway link -p pilotos -e staging -s aethos-api
bash scripts/railway_apply_aethos_api_defaults.sh
railway variable set --service aethos-api DATABASE_URL='${{Postgres.DATABASE_URL}}'
```

## Worker service

**Staging today:** there is no separate `aethos-worker` Railway service. Durable agent jobs run **embedded** in `aethos-api` via `job_executor` (background thread in the same process). Setting `DATABASE_URL` on `aethos-api` is sufficient for writer + reader to share Postgres.

When you add a standalone worker (`python -m aethos_core.runtime.worker_main`), set the **same** `DATABASE_URL` on that service:

```bash
railway variable set --service aethos-worker DATABASE_URL='${{Postgres.DATABASE_URL}}'
```

The worker executes durable jobs that may call `canvas_render`; it must point at the same Postgres as the API.

## Startup guard

On boot, the API logs a **CRITICAL** message if hosted mode runs without `DATABASE_URL` while durable jobs or a standalone worker are enabled. Set `HOSTED_SHARED_STORE_STRICT=true` to fail fast instead of silent data loss.

## Verify canvas cross-process

After deploy, grep logs on api (and worker if deployed):

- `canvas_render write session_id=… backend=postgres`
- `canvas_state read request_session_id=… view_count=N backend=postgres`

With Postgres configured, `view_count` should be > 0 on the API after a successful render.

## No per-service canvas volume

Do not rely on `data/canvas/canvas.json` on ephemeral disk. Helm uses a shared PVC; Railway must use `DATABASE_URL`.
