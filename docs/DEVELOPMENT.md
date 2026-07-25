# Development

## Working copy

Clone the repository into any local projects directory. Commands in this guide
assume the repository root is the current directory.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

cd web
npm ci
```

See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for running the API and web UI.

## Repository layout

```text
aethos_core/     Python runtime, API, governance, providers, and operations
aethos_sdk/      Governed plugin interfaces
provider_skills/ Provider-specific operational skill definitions
skills/          Operator skill definitions
web/             Next.js Mission Control UI
tests/           Unit, integration, regression, and certification tests
deploy/          Deployment manifests and examples
scripts/         Maintenance, validation, and report utilities
```

## Workflow

Create a focused branch and open a pull request:

```bash
git switch -c feature/short-description
git add <changed-files>
git commit -s -m "area: concise description"
git push -u origin HEAD
```

Do not push directly to `main`. Read [CONTRIBUTING.md](../CONTRIBUTING.md) for
DCO sign-off, testing, documentation, security, and review requirements.

## Engineering standards

- Preserve the separation between read-only inspection and governed mutation.
- Keep one authoritative implementation for each decision or state transition.
- Do not log, serialize, or return credentials.
- Scope persistent state by tenant, organization, workspace, and session where
  applicable.
- Add regression tests for bug fixes and negative tests for security controls.
- Prefer public, stable terminology over implementation-phase or work-order names.
- Update `.env.example` and public docs when configuration changes.

Run the full checks described in [TESTING.md](TESTING.md) before final review.
