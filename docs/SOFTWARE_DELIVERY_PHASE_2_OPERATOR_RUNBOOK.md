# Software Delivery Phase 2 — Operator Runbook (FIX 126)

Governed operator path for FIX **125A–125I**.  
Freeze: [SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md](./SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md)  
Index: [SOFTWARE_DELIVERY_PHASE_2_INDEX.md](./SOFTWARE_DELIVERY_PHASE_2_INDEX.md)

```text
software_delivery_lane != infrastructure_mutation_lane
```

---

## Exact operator sequence (do not skip)

Run in order. Include approval phrases where noted.

```text
analyze github issue owner/repo#N
create implementation plan
approve implementation planning          (+ planning phrase)
create implementation branch             (+ branch create phrase)
propose files to change                    (or: propose patch files)
generate patch intent
approve patch proposal                     (+ patch phrase)
apply approved patch to workspace          (+ apply phrase)
run workspace verification
create software delivery pr draft
run github pr creation preflight
approve github pr creation preflight       (+ preflight phrase)
push governed branch to github             (+ push phrase + preview ack)
open governed github pull request            (+ PR open phrase)
→ human review on GitHub (out of band)
```

Optional diagnostics between steps: `show software delivery timeline`

---

## Required approval phrases (125A–125I)

| Stage | Exact phrase |
|-------|----------------|
| 125A planning | `I approve this governed software delivery implementation plan for human review.` |
| 125B branch | `I authorize creating the governed implementation branch for this software delivery plan.` |
| 125C patch | `I approve this governed software delivery patch proposal for bounded application.` |
| 125D apply | `I authorize applying the approved patch proposal to the governed software delivery workspace.` |
| 125D rollback | `I authorize rolling back the governed software delivery workspace to the pre-apply snapshot.` |
| 125G preflight | `I authorize proceeding with governed GitHub PR creation after this preflight.` |
| 125H push | `I authorize pushing the governed workspace changes to the GitHub feature branch.` |
| 125H ack | `I acknowledge the governed branch push mutation preview from FIX 125G.` |
| 125I PR open | `I authorize opening the governed GitHub pull request for human review.` |

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| GitHub token | Credential Center / repo scope |
| Issue | `analyze github issue pilotmain/AethOS#80` |
| Cert rehearsal | `AETHOS_CERTIFICATION_MODE=true make certify` |

```bash
SOFTWARE_DELIVERY_PHASE_2_FROZEN=true
SOFTWARE_DELIVERY_GITHUB_BRANCH_PUSH_ENABLED=true
SOFTWARE_DELIVERY_GITHUB_PR_OPEN_ENABLED=true
```

---

## Step reference

### 125A — Issue & plan

| Command |
|---------|
| `analyze github issue owner/repo#N` |
| `create implementation plan` |
| `approve implementation planning` |

### 125B — Branch

| Command |
|---------|
| `create implementation branch` |
| `show implementation branch status` |

### 125C — Patch

| Command |
|---------|
| `propose files to change` |
| `generate patch intent` |
| `show patch diff preview` |
| `approve patch proposal` |

### 125D — Workspace

| Command |
|---------|
| `apply approved patch to workspace` |
| `show governed workspace diff` |
| `rollback workspace changes` |
| `show workspace apply status` |

### 125E — Verification

| Command |
|---------|
| `run workspace verification` |
| `show workspace verification report` |

### 125F — PR draft

| Command |
|---------|
| `create software delivery pr draft` |
| `show pr draft status` |

### 125G — Preflight (no mutation)

| Command |
|---------|
| `run github pr creation preflight` |
| `approve github pr creation preflight` |

### 125H — Branch push (first GitHub mutation)

| Command |
|---------|
| `push governed branch to github` |
| `show governed branch push report` |

### 125I — PR open (second GitHub mutation)

| Command |
|---------|
| `open governed github pull request` |
| `show governed github pr report` |

### Human review

Merge and deploy **outside** this lane.

---

## Troubleshooting

### Verification blocked

- **Symptom:** `workspace_verification_not_passed`, PR draft blocked  
- **Fix:** `run workspace verification`; read `show workspace verification report`  
- **If failed:** fix workspace tree; `rollback workspace changes` + rollback phrase; re-apply from 125D  

### Workspace rollback

- **When:** bad apply, wrong files, verification cannot pass  
- **Command:** `rollback workspace changes` + rollback phrase  
- **Then:** fix patch proposal (125C) and re-apply (125D)  

### Preflight rejection

- **Symptom:** `github_pr_preflight_not_passed` / failed checks  
- **Fix:** `show github pr creation preflight report`; resolve auth, package size, branch readiness  
- **Re-run:** `run github pr creation preflight` → `approve` with phrase  

### Protected branch violation

- **Symptom:** `protected_branch_violation` on push  
- **Cause:** branch name is `main`/`master` or default branch  
- **Fix:** use governed feature branch from 125B (`aethos/sd-...`)  

### GitHub auth failure

- **Symptom:** `github_auth_scope`, `github_token_missing`  
- **Fix:** configure GitHub token in Credential Center; re-run preflight  

### Idempotent replay

- **Symptom:** “already pushed” / “idempotent replay”  
- **Expected:** same `idempotency_key`; no duplicate mutation  
- **Action:** proceed to next stage or `show` report for URL/SHA  

### Phrase blocked

- Copy **exact** phrase from table above (no paraphrasing)  

---

## Evidence

```text
show software delivery timeline
```

---

## Out of scope

- Railway Phase 1 runbook
- FIX 125J / 127 multi-agent (deferred)
- Merge, deploy, production promotion
