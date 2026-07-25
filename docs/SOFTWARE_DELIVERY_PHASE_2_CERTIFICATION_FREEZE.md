# Software Delivery Phase 2 — Certification Freeze (FIX 126)

**Status:** FROZEN at FIX 126  
**Schema:** `software_delivery_phase_2_v2`  
**Frozen commit:** `3dfa0f9` (initial FIX 126 freeze; update contract on re-freeze only)

---

## Objective

Freeze and certify the completed governed software delivery loop (FIX 125A–125I).  
**Non-feature only:** documentation, certification, freeze flags, operator runbooks, regression prevention.

**No new mutation capability** in FIX 126.

---

## Frozen Phase 2 Software Delivery Loop

```text
issue
→ implementation plan
→ governed branch
→ bounded patch proposal
→ governed workspace apply
→ workspace verification
→ PR draft
→ GitHub preflight
→ governed branch push
→ governed PR open
→ human review
```

---

## Frozen lane list

| Lane | Fix | Module owner |
|------|-----|--------------|
| Issue planning | 125A | `issue_plan_service` |
| Branch orchestration | 125B | `branch_orchestration_service` |
| Patch proposal | 125C | `patch_proposal_service` |
| Workspace apply | 125D | `workspace_application_service` |
| Workspace verification | 125E | `workspace_verification_service` |
| PR drafting | 125F | `pr_draft_service` |
| GitHub preflight | 125G | `github_pr_preflight_service` |
| Governed branch push | 125H | `branch_push_service` |
| Governed PR open | 125I | `github_pr_open_service` |

Unified router: `software_delivery_router` → `route_id=software_delivery_issue_plan`

---

## Frozen invariants

1. **Governed workspace only** — file writes under `data/software_delivery_workspaces/{plan_id}/tree/` until 125H
2. **No repo mutation outside approved stages** — 125H/I only, feature branch + PR open
3. **No merge** — human merge on GitHub, out of band
4. **No deploy** — infrastructure lane separate
5. **No Railway coupling** — `software_delivery_lane != infrastructure_mutation_lane`
6. **Human review mandatory** — loop terminal state after PR open
7. **Exact approval phrases required** — no fuzzy matching
8. **Receipts + timelines mandatory** — `show software delivery timeline`
9. **Idempotency mandatory** — replay receipts, not duplicate mutations
10. **Rollback snapshots mandatory** — workspace rollback (125D) with approval phrase

---

## Explicitly NOT included (blocked after FIX 126)

- auto-merge
- deploy
- Railway mutation
- production deploy
- arbitrary shell execution
- unrestricted file mutation
- dependency installation
- autonomous PR approval
- autonomous rollout promotion
- autonomous rollback
- multi-agent concurrent mutation
- self-authorizing execution

Future capabilities require **explicit phase sign-off** and contract update.

---

## Certification minimums

| Baseline | Minimum |
|----------|---------|
| Certification modules | **19** |
| Passing tests | **61** |

Current certified suite: **20** modules, **70** tests (at or above baseline).

```bash
make certify
```

---

## Regression protection

Certification fails if:

- Module count drops below **19**
- Test count drops below **61**
- Merge/deploy enabled in software delivery contracts
- Railway imports appear under `aethos_core/software_delivery/`
- GitHub PR open bypasses verification or preflight gates
- Route ownership drifts from `software_delivery_issue_plan`
- Loop order changes without contract update

Test module: `tests/certification/test_software_delivery_phase_2_freeze_certification.py`

---

## Machine-readable contract

`aethos_core/software_delivery/software_delivery_phase_2_contract.py`

Key flags:

```python
SOFTWARE_DELIVERY_PHASE_2_FROZEN = True
SOFTWARE_DELIVERY_MIN_CERT_MODULES = 19
SOFTWARE_DELIVERY_MIN_TEST_COUNT = 61
```

---

## Operator documentation

- [SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md)
- [SOFTWARE_DELIVERY_PHASE_2_INDEX.md](./SOFTWARE_DELIVERY_PHASE_2_INDEX.md)

---

## Deferred until after FIX 126

| Item | Notes |
|------|-------|
| FIX 125J | Bounded multi-agent roles |
| FIX 127 | Expanded agent orchestration |
| Governed merge / deploy promotion | Future, separate lanes |

---

## Version history

| Version | Fix | Notes |
|---------|-----|-------|
| v2 | FIX 126 | Full spec alignment: index, invariants, regression baselines |
| v1 | FIX 126 | Initial freeze + runbook |
| impl | 125A–125I | Governed loop implementation |
