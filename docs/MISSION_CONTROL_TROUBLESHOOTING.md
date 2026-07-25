# Mission Control troubleshooting

Start with the environment doctor and API health:

```bash
aethos doctor
curl -fsS http://127.0.0.1:8010/api/v1/health
```

## UI cannot reach the API

- Confirm the API process is listening on the configured port.
- Check `NEXT_PUBLIC_API_BASE` in `web/.env.local`.
- Review browser developer tools for network, CORS, or authentication errors.
- If a reverse proxy adds a path prefix, ensure both frontend and backend base
  paths match.

## Empty or stale operational views

- Confirm the active account, organization, workspace, and session.
- Refresh provider inventory and the affected panel.
- Check that the provider credential is present and validated.
- Inspect API logs for timeouts or rejected requests.
- Treat a view without current evidence as unknown; do not approve based on it.

## Approval is unavailable or blocked

- Expand the preflight and read every blocker.
- Confirm all required target fields are resolved.
- Complete earlier gates before retrying a later stage.
- Refresh if another operator or session may have consumed the approval.
- Do not bypass a blocked approval with a direct CLI or provider action.

## Execution completed without verification

- Use the execution identifier to inspect job state and provider evidence.
- Run a read-only provider status check.
- Verify the intended resource, version, branch, and environment.
- If the result is ambiguous, leave the operation unverified and follow the
  documented recovery or rollback path.

## Credential errors

- Re-enter or rotate the credential through the credential interface.
- Use the least privilege needed for the requested capability.
- Confirm the credential belongs to the expected tenant and provider account.
- Never paste tokens into issues, logs, screenshots, or chat transcripts.

## Suspected governance regression

Stop mutation work if Mission Control appears to call a provider directly,
replays an approval, crosses tenant scope, or exposes a secret. Preserve redacted
evidence and follow [../SECURITY.md](../SECURITY.md).

For general runtime problems, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
