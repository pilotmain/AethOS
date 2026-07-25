# Self-host AethOS

Run your own personal AethOS control plane on your machine or a VPS — your data,
your hardware, your model keys. No hosted dependency.

## Quick start

```bash
cp .env.selfhost.example .env
# edit .env: set AETHOS_VAULT_KEY and one model key (Anthropic or OpenRouter)
docker compose -f docker-compose.local.yml up -d
open http://localhost:3000
```

The first screen opens the single-user onboarding flow without the hosted
multi-tenant sign-in.

## What self-host mode does

Setting `SELF_HOST=true` (already set in `docker-compose.local.yml`) puts AethOS in
single-user mode:

- **No hosted tenant gate** — the multi-tenant sign-in/onboarding flow is turned
  off.
- **No auth wall** — `auth_enabled` is forced off; you're not locked out of your own
  instance. (Put it behind your own VPN / reverse-proxy auth if exposing it.)
- **You are the owner** — `is_platform_owner` returns true, so you get the Owner
  console and every governed surface on your own box.

These are enforced in `Settings._apply_self_host_profile` (config.py) and
`rbac.is_platform_owner`, so even a stray hosted-style `.env` can't re-enable the
gate under self-host.

## What stays the same

- **Governance is intact.** Mutations still require your approval in the Approval
  Inbox, and every action is still audited. Self-host removes the *tenant gate*, not
  the *safety model*.
- **Bring your own keys.** AethOS only ever calls the providers you connect
  (model APIs, GitHub/Vercel/Railway, messaging channels). Connect them from
  Settings → Providers / Channels, or via `.env`.

## Data & persistence

Everything (encrypted credential vault, memory, agent artifacts, research) lives in
the `aethos_data` Docker volume on your machine. Keep `AETHOS_VAULT_KEY` safe — it
decrypts the vault; losing it means re-entering provider keys.

## Updating

```bash
git pull
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d
```

## Exposing it (optional)

The local compose binds to `localhost`. To reach it from other devices, front it
with a reverse proxy (Caddy/nginx) that adds TLS and your own auth — don't expose
the raw ports to the internet, since self-host mode intentionally has no auth wall.
