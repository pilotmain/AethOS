# Testing

## Backend

```bash
source .venv/bin/activate
python -m compileall -q aethos_core aethos_sdk
ruff check --select=E9,F63,F7,F82 aethos_core aethos_sdk
python -m pytest tests -q -p no:cacheprovider
```

Run a focused test while developing, then run the full suite before requesting
final review.

## Frontend

```bash
cd web
npm ci
npm run typecheck
npm test
npm run build
```

## Repository and security gates

```bash
python scripts/check_public_release.py
gitleaks dir . --redact --config .gitleaks.toml
```

CI also scans Git history for secrets, audits dependencies, generates SBOMs, and
runs CodeQL. Test credentials must be unmistakably synthetic and annotated with a
narrow `gitleaks:allow` comment only when needed.

## Test design

- Tests must be deterministic and must not require production credentials.
- Mock network and provider mutations unless a test is explicitly isolated as a
  live integration test.
- Use temporary directories for credentials, artifacts, and runtime state.
- Cover success, denial, missing-input, cross-tenant, replay, and redaction paths.
- A bug fix should include a regression test that fails without the fix.

## Useful focused checks

```bash
python -m pytest tests/test_beta_smoke_harness.py -q -p no:cacheprovider
python -m pytest tests/test_chat_20_turn.py -q -p no:cacheprovider
bash scripts/run_behavioral_corpus.sh
```

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for pull-request requirements.
