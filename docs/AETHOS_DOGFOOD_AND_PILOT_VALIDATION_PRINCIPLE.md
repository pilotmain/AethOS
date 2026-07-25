# AethOS Dogfood & Pilot Validation Principle

**Status:** Operational principle (evidence-driven phase)  
**Applies to:** FIX 181–183 pilot validation, multi-repo dogfood, FIX 184+ scaling, POST_FIX_366 execution era  
**Related:** [AETHOS Governance Friction & Human Approval Principle](./AETHOS_GOVERNANCE_FRICTION_AND_APPROVAL_PRINCIPLE.md), POST_FIX_366 Architecture Completion Review

---

## Purpose

AethOS has reached a maturity point where architecture is no longer the primary constraint.

The primary constraint is now **operational evidence**.

The goal of the next phase is to validate whether the governed delivery system can successfully perform real work on real repositories while preserving governance, auditability, replayability, and human trust.

This phase shifts emphasis from architecture creation to evidence collection.

---

## Maturity transition

**Previous question:** Can the governed delivery architecture exist without backdoors?

**Current question:** Can the governed delivery architecture successfully complete real work with acceptable human effort?

This represents the transition from:

```text
Design Validation → Operational Validation
```

---

## Pilot validation progression

| FIX | Question | Purpose | Output |
|-----|----------|---------|--------|
| **182** | Ready? | Determine whether a repository is suitable for pilot execution | Readiness assessment |
| **181** | Run | Execute one governed software delivery loop on one bounded issue | Pilot execution receipts |
| **183** | Trust? | Determine whether the pilot outcome justifies future use | Pilot validation assessment |
| **184** | Align? | Validate patch targets match issue scope before patch proceeds | Intent alignment assessment |
| **185** | Fidelity? | Preserve GitHub issue scope through intake and planning | Issue intake scope fidelity |
| **186** | Freeze? | Freeze Pilots 1–3 into institutional trust baseline before multi-repo expansion | Dogfood pilot trust report freeze |
| **187** | Expand? | Govern independent per-repo trust — no inherited trust across repositories | Independent repository trust expansion contract |
| **188** | Arc | Execute PilotOS UI pilot 1→3 and track trust-earning lifecycle | PilotOS UI pilot arc orchestrator |
| **189+** | Scale | Execute Phase 2 pilot arcs on additional approved repositories | Operational confidence growth |

See also:

- FIX 182 — Repo pilot readiness dashboard
- FIX 183 — Pilot validation & trust board
- FIX 184 — Issue intent alignment & patch target validation
- FIX 185 — Issue intake scope fidelity
- FIX 186 — Dogfood pilot trust report freeze
- FIX 187 — Independent repository trust expansion
- FIX 188 — PilotOS UI pilot arc orchestrator
- Dogfood pilot 2 — alignment gate regression
- Dogfood pilot 3 — full loop through PR Open
- FIX 181 — End-to-end repo development pilot harness
- FIX 181–186 manual test gate

---

## Dogfood repository selection model

The objective is not broad coverage. The objective is **evidence**.

Evaluate:

| Repository | Ready | Blockers | Recommended first issue |
|------------|-------|----------|-------------------------|
| AethOS | **Yes** (8/8) | none | Create small bounded issue on `pilotmain/AethOS` (e.g. doc fix); best first pilot — cert stack + self-dogfood |
| PilotOS UI | **Yes** (8/8) | none | Create issue on `pilotmain/pilot-os-ui`; no open issues today |
| Atlas Trader | **Yes** (8/8) | none | Create issue on `pilotmain/atlas-trader`; no open issues today |
| Nexora | **Yes** (8/8) | none | Create issue on `pilotmain/nexora-monorepo-starter`; no open issues today |

_Assessed 2026-05-29 via FIX 182 (`build_repo_pilot_readiness_dashboard`). GitHub auth: 142 accessible repos. All four repos verified accessible. No open GitHub issues on any candidate repo at assessment time — first pilot requires creating a small bounded issue._

**Selection principle:** Choose the easiest repository, smallest bounded issue, and lowest blast radius.

The first successful pilot is more valuable than four incomplete pilots.

---

## Operational success metrics

The primary metric is **not**:

- Tests passed
- Certification count
- Governance layer count

The primary metric is:

### Human effort per successful issue

Measured by:

- Approval count
- Re-engagement count
- Manual intervention count
- Human review duration
- Total operator touches

---

## Pilot outcome classification

### Scenario A — Clean success

**Characteristics:**

- Pilot completes
- Minimal intervention
- Governance respected
- Evidence complete

**Meaning:** Pipeline is operationally viable.

### Scenario B — Successful but friction heavy

**Characteristics:**

- Pilot completes
- Excessive approvals
- Excessive re-engagement
- Repeated operator interruptions

**Meaning:** Governance friction tuning required. Architecture remains valid.

### Scenario C — Failed pilot

**Characteristics:**

- Pilot stops at a specific stage
- Evidence identifies exact failure point

**Meaning:** Investment should focus on the failed stage. Do not redesign unrelated architecture.

---

## FIX 183 requirements

FIX 183 must compose FIX 181 artifacts and audits only.

**Invariant:** `validation ≠ re-execution`

FIX 183 must never re-run pilot actions.

**Required outputs:**

- Stages completed
- Stage stopped at
- Approval count
- Re-engagement count
- Manual intervention points
- Human effort score
- Issue risk tier
- Trust recommendation (`yes` | `conditional` | `no`)

**Question answered:** Would we trust AethOS to handle a larger issue?

---

## Governance friction alignment

This phase directly supports [AETHOS_GOVERNANCE_FRICTION_AND_APPROVAL_PRINCIPLE.md](./AETHOS_GOVERNANCE_FRICTION_AND_APPROVAL_PRINCIPLE.md).

**Core principle:** Governance scales with risk. Governance does not scale with workflow length.

- Low-risk bounded work → minimal operator interruption
- Higher-risk work → explicit re-engagement

---

## Current maturity assessment

| Capability | Estimated maturity |
|------------|-------------------|
| Governance operating system | 90–95% |
| Real repo pilot capability | ~80% |
| Multi-repo dogfood readiness | 70–80% |
| Public end-user readiness | 50–60% |

These percentages are directional only and must eventually be replaced by pilot evidence.

---

## Next recommended sequence

- AethOS first dogfood pilot execution plan

1. Run FIX 182 readiness assessment on all candidate repositories.
2. Select the repository with the lowest blocker count.
3. Select the smallest bounded issue.
4. Run FIX 181 pilot.
5. Capture evidence bundle, replay, timeline, and audit artifacts.
6. Execute FIX 183 validation.
7. Re-run issue #1 as dogfood pilot 2 to verify FIX 184 alignment gate.
8. Decide whether to expand to additional repositories.

---

## Architectural principle

The remaining uncertainty is no longer:

> "Can we design the system?"

The remaining uncertainty is:

> "Can the system repeatedly complete real work with acceptable human effort?"

Future roadmap decisions should be driven by pilot evidence rather than architectural speculation.
