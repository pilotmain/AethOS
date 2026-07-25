# Contributing to AethOS

Thank you for helping improve AethOS. This guide defines the contribution
controls used to keep changes reviewable, licensed, secure, and consistent with
the project's governed-execution principles.

## Before you start

- Search existing issues and pull requests before proposing duplicate work.
- Use an issue for substantial features, architecture changes, or behavior that
  affects security, approvals, credentials, tenancy, or provider mutations.
- Report vulnerabilities through [SECURITY.md](SECURITY.md), never a public
  issue.
- Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Maintainers may close proposals that conflict with the project scope or safety
model. Opening an issue does not reserve implementation work unless a maintainer
has agreed on the direction.

## Development setup

Use Python 3.11+ and Node.js 24 LTS.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

cd web
npm ci
```

Never commit `.env`, credentials, access tokens, customer data, captured browser
artifacts, or production logs. Use synthetic, clearly fake fixture data.

## Change workflow

1. Fork the repository or create a focused branch from current `main`.
2. Keep each pull request limited to one coherent change.
3. Add or update tests for behavior changes.
4. Update public documentation and `.env.example` when configuration changes.
5. Run the relevant checks locally.
6. Sign off every commit under the Developer Certificate of Origin.
7. Open a pull request using the repository template and respond to review.

```bash
git commit -s -m "area: concise description"
```

The sign-off adds `Signed-off-by: Name <email>` to the commit. It certifies the
statements in [DCO.md](DCO.md); it is not a copyright assignment.

## Required checks

Run the smallest relevant tests while developing, then run the full gates before
requesting final review:

```bash
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q aethos_core aethos_sdk
ruff check --select=E9,F63,F7,F82 aethos_core aethos_sdk
python scripts/check_public_release.py

cd web
npm run typecheck
npm test
npm run build
```

Changes must also pass CI, security scanning, and the DCO sign-off check.
Maintainers may require additional focused tests for high-risk paths.

## Review controls

Pull requests require:

- passing required status checks;
- review from a maintainer or applicable code owner;
- no unresolved review conversations;
- no secrets, personal data, generated runtime state, or unrelated changes;
- clear user impact, test evidence, and rollback notes when risk is non-trivial.

Security, authentication, credential, approval, mutation, tenancy, workflow,
license, and governance changes receive heightened review. A maintainer may ask
for a smaller patch, threat analysis, migration plan, or additional reviewer.

Do not force-push after review unless necessary; if you do, tell reviewers what
changed. Maintainers merge approved changes and may squash commits.

## License of contributions

AethOS is licensed under Apache-2.0. Unless you explicitly state otherwise, an
intentional contribution is submitted under Apache-2.0 in accordance with
section 5 of [LICENSE](LICENSE). You retain copyright in your original work.
