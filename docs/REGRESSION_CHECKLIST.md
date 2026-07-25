# Regression Checklist — Manual QA

Repeatable checklist for release validation. Run after major changes or before demos.

## Environment

- [ ] `aethos doctor` — no FAIL checks
- [ ] Mission Control → Operational Health — overall healthy or degraded (not unhealthy)
- [ ] Configuration Center — safe defaults verified

## Telegram

- [ ] `GET /api/v1/channels/telegram/status` — expected state for your config
- [ ] Send test message; receive governed response
- [ ] Typing indicator (if enabled)

## Research

- [ ] Research question returns artifact (or clear misconfiguration error)
- [ ] Mission Control → Research Intelligence shows artifacts

## Browser Evidence

- [ ] Browser status ready (if enabled) or clearly disabled
- [ ] Evidence capture produces audit entry

## Provider Inventory

- [ ] Credential Center loads without secrets exposed
- [ ] Revalidate action returns structured result

## Mutation Preflight

- [ ] Mutation execution blocked when disabled
- [ ] Preflight required before sandbox execution

## Engineering Preflight

- [ ] Generate preflight from recommendation
- [ ] Approval gate blocks execution until approved

## Workspace Runtime

- [ ] Workspace terminal preflight (governed)
- [ ] Policy denial audited

## Operational Presence

- [ ] Presence cycle runs (readonly)
- [ ] Feed deduplicated; no repo-drift spam on deployment questions

## Reliability Trust

- [ ] Reliability state loads
- [ ] Confidence bounded; explainability present
- [ ] Recovery actions require approval

## Demo Mode

- [ ] Enable demo — synthetic data labeled DEMO DATA
- [ ] Disable demo — overlay removed

---

**Sign-off:** _______________ **Date:** _______________
