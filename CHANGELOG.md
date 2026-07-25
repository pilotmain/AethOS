# Changelog

Notable changes to AethOS are recorded here. The project intends to follow
Semantic Versioning once public versioned releases begin.

## 0.2.1 — 2026-07-24

### Added

- Interactive onboarding in the one-line installer (macOS/Linux/Windows):
  guided AI-provider setup with live key validation for all ten providers,
  self-host mode, vault-key generation, optional login passphrase, web
  research, and Telegram — written to `.env` so the first run is ready to use.
- Install lifecycle commands: `--update`, `--reinstall` (keeps `.env` on
  request), `--uninstall`, `--onboard`, `--no-onboard`, `--non-interactive`,
  and an update/reinstall/onboard menu when an install already exists.
- Version currency gate in `run.sh`/`run.ps1`: daily release check, update
  reminders, and a configurable 30-day limit before an update is required.

## 0.2.0 — 2026-07-24

Initial public release.

### Added

- Apache-2.0 open-source licensing and attribution files.
- Contributor DCO, governance, conduct, support, issue, and pull-request policies.
- Public documentation index and open-source release controls.

### Changed

- Aligned package metadata, source headers, tests, and documentation with the
  Apache-2.0 license.
- Hardened repository secret-scanning scope and contributor review controls.
