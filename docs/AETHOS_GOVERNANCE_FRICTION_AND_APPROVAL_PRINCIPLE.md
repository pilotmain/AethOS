# AethOS Governance Friction & Human Approval Principle

**Status:** Architectural Principle (additive only)  
**Contract:** [`aethos_core/governance/governance_friction_approval_contract.py`](../aethos_core/governance/governance_friction_approval_contract.py)

Applies to FIX 170+, mission planning, multi-agent delivery, execution coordination, lane admission, and future human-approved execution systems.

This principle must not break any existing functionality, governance controls, certifications, freezes, approval gates, replay guarantees, or constitutional boundaries.

---

## Purpose

As AethOS evolves from a **governed execution platform** toward an **institutional delivery system**, human approvals must remain meaningful.

The purpose of governance is not to maximize approval count. The purpose is to preserve:

- Human sovereignty
- Accountability
- Safety
- Auditability
- Constitutional integrity

…while allowing operators to accomplish meaningful work with minimal unnecessary interruption.

---

## Core principle

### Governance should scale with risk, not workflow length

AethOS must not require additional approvals simply because a workflow contains many internal steps.

Approval requirements **should** scale with:

- Risk
- Authority
- Blast radius
- Boundary crossings
- Organizational impact

Approval requirements **should not** scale with:

- Number of agents
- Number of stages
- Number of generated artifacts
- Number of internal transitions
- Workflow length

---

## Approval fatigue prevention

AethOS shall seek the minimum number of human approval events necessary to preserve human sovereignty, accountability, safety, governance integrity, and institutional trust.

Repeated approvals for a single continuous bounded mission should be avoided whenever governance guarantees remain intact.

Approval fatigue weakens governance because operators eventually stop evaluating approval requests. Meaningful governance requires meaningful approvals.

---

## Current architectural alignment

The existing platform already follows this principle for most cognition layers.

### Tier 0 — Cognition without authority

No approval required. Examples:

- Constitutional cognition (FIX 150–163)
- Mission planning (FIX 164)
- Multi-agent deliberation (FIX 165)
- Execution handoff (FIX 167)
- Work package generation (FIX 168)
- Readiness & lane admission (FIX 169)
- Mission Control observability, operational memory, governance simulation

These layers analyze, plan, reason, deliberate, simulate, and recommend — but do not execute authority.

```text
cognition ≠ authority
```

---

## Approval tier model

| Tier | Examples | Approval |
|------|----------|----------|
| **0** — Read-only cognition | Analysis, deliberation, planning, evidence, replay, simulation | No |
| **1** — Low-risk bounded activities | Work packages, readiness, non-mutating artifacts | Prefer mission authorization |
| **2** — Low-risk external mutations | Branch push, PR open, review request, issue updates | Yes, preferably bundled |
| **3** — High-risk mutations | Infrastructure, deploy, environment, rollback | Explicit approval |
| **4** — Critical authority events | Production deploy/rollback, policy, security, financial | Strong explicit approval |

### Tier 2 preferred model

```text
Approve Mission
```

not

```text
Approve Branch → Approve Push → Approve PR → Approve Review
```

for the same bounded objective.

---

## Mission authorization philosophy

Future execution systems should prefer **Approve Mission** over **Approve Every Step**.

Mission authorization should define:

- Scope
- Duration
- Allowed lanes
- Blast-radius ceiling
- Agent boundaries
- Approval boundaries

AethOS may continue bounded work inside the approved envelope. Humans are re-engaged only when risk, scope, or protected boundaries materially change.

### Human re-engagement triggers

**Required when:**

- Production systems are affected
- Governance authority is exercised
- Organizational risk materially changes
- Security boundaries change
- Constitutional decisions are required
- Mission scope expands beyond authorization

**Not required when:**

- Internal workflow stages complete
- Agents finish bounded packages
- Readiness checks pass
- Reports, evidence, or planning artifacts are produced
- Deliberation completes

---

## Non-breaking requirement

This principle must never weaken or remove:

- Railway governance protections
- Production governance controls
- Software delivery gates (FIX 125A–126 freeze)
- Mission Control controls
- Constitutional governance layers
- Human decision authority
- Replay, audit, and certification guarantees

Future enhancements reduce approval repetition while preserving all governance guarantees.

---

## Future direction (FIX 170+)

```text
Human Decision
      ↓
Mission Authorization        ← bounded work envelope (FIX 170)
      ↓
Execution Handoff
      ↓
Work Packages
      ↓
Readiness Validation
      ↓
Bounded Execution
      ↓
Human Re-Engagement (only when required)
```

**FIX 170 success criterion:** Mission Authorization wraps bounded work **within** existing gates — it does not bypass them.

```text
Human Decision → Mission Authorization → Bounded Work Envelope → Existing Gates
```

not

```text
Human Decision → Mission Authorization → Bypass Existing Gates
```

### FIX 170 certification requirements (pre-declared)

Mission authorization **cannot expand authority** beyond the human-granted envelope. Certification must assert:

- Authorization for `software_delivery` cannot silently include Railway or production lanes
- Tier 1–2 authorization cannot satisfy Tier 3–4 approval requirements
- Bounded work routes **through** existing gates, not around them
- Human re-engagement on scope, lane, or tier escalation

Machine-readable: `FIX_170_CERTIFICATION_REQUIREMENTS` in the governance friction contract.

---

## Constitutional governance statement

Human sovereignty remains absolute.

AethOS may analyze, plan, deliberate, coordinate, prepare, and recommend.

AethOS may not replace human authority, remove required approvals, expand mission scope autonomously, cross protected governance boundaries, or execute critical authority events without authorization.

---

## Desired end state

```text
AethOS performs most bounded work.
Humans decide what matters.
```

Governance remains strong because approvals remain meaningful. Approval friction scales with risk. Human sovereignty remains intact. Operator productivity remains high.

---

## Related

- [AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md](./AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md)
- AETHOS_PHASE_2_READINESS_CONTRACT.md
- [MISSION_CONTROL_INDEX.md](./MISSION_CONTROL_INDEX.md)
- [SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md](./SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md)
