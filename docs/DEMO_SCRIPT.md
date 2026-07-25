# AethOS Product Demo Script

Polished demo flow for first-time users and stakeholders. Enable **Demo Mode** if real credentials are unavailable.

## Preparation

```bash
./install.sh && ./run.sh
aethos demo enable
```

Mission Control → Enterprise Readiness → Demo Mode → Enable demo

Confirm: all sample data labeled **DEMO DATA**

---

## Act 1 — Research from Telegram (2 min)

**Prompt (Telegram or chat):**

> What are the latest best practices for operational AI platforms?

**Show:**

- Research lane response with citations
- Mission Control → Research Intelligence → artifact replay

---

## Act 2 — Operational awareness (2 min)

**Prompt:**

> What changed in the last 2 hours? Any recurring deployment instability?

**Show:**

- Operational Presence brief (deduplicated, deployment-focused)
- Attention Center with priority discipline
- No repo-drift spam

---

## Act 3 — Risk detection (2 min)

**Show Mission Control:**

- Operational Intelligence → Active Anomalies
- Operational Trust → Reliability Authority (truth state, bounded confidence)
- Correlation Graph (workflow → deployment cascade)

---

## Act 4 — Governed engineering (3 min)

**Scenario:** Repeated workflow instability detected

**Show:**

- Recommendation Queue → contextual preflight suggestion
- Approve engineering preflight (human approval required)
- Sandbox Executions → patch applied in sandbox
- Validation Center → pytest results
- PR Drafts Center → governed PR draft (no auto-merge)

---

## Act 5 — Browser evidence (1 min)

**Show:**

- Browser Evidence → captured screenshot/metadata
- Audit trail for governed capture

---

## Act 6 — Operational Trust (1 min)

**Show:**

- Trust Metrics → global reliability score
- Confidence Center → bounded confidence explanation
- Governance Drift → adaptive tier (if pressure elevated)

---

## Closing message

> AethOS observes, correlates, prioritizes, and recommends — but never self-authorizes. Every mutation requires human approval, bounded confidence, and audit.

## Disable demo

```bash
aethos demo disable
```

---

## Regression

After demo, run [REGRESSION_CHECKLIST.md](REGRESSION_CHECKLIST.md).
