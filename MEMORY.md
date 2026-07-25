# AethOS Memory — Hierarchy and Retention Contract

This file is a runtime behavior contract. It documents how AethOS prioritizes
operational context; it is not a record of private operator data or project
planning.

AethOS uses layered memory. Each layer has a scope, precedence, and reconstruction rule.

## Memory layers

| Layer | Scope | Typical retention |
|-------|--------|-------------------|
| Active turn context | Current message and immediate routing state | Current turn |
| Active task frame | Clarifications, pending confirmations, offered retries | Until resolved or superseded |
| Active operational thread | Provider, project, environment, service, operation, jobs, status | 8 hours default TTL |
| Job truth ledger | Preflight, execution, verification, failure truth | Durable while job exists |
| Provider topology memory | Inventory, bindings, service graph | Refreshed on discovery; bindings persist |
| Source binding memory | GitHub repo ↔ provider service mapping | Durable until reconciled |
| Workspace artifact memory | Local/workspace investigation artifacts | Session/project scoped |
| Conversation summary memory | Compressed turn history for continuity | Session scoped |
| Long-term preference/project memory | Operator preferences and stable project facts | Long-lived |

## Memory precedence

When answering operational questions, AethOS resolves evidence in this order:

1. Fresh runtime and job evidence
2. Active operational thread
3. Provider topology and inventory
4. Source binding memory
5. Workspace artifacts
6. Conversation memory
7. Long-term memory

Higher layers outrank lower layers for factual claims about current system state.

## Reconstruction rule

AethOS must not answer **"I don't have context"** until it has checked:

- active thread (including expired-thread recovery)
- recent jobs in the session and global job ledger
- provider topology for named services/resources
- service name or job ID in the user prompt
- recent operational evidence bundles
- source binding records

If reconstruction succeeds, AethOS continues as one operational partner — even when the active mutation thread TTL expired.

## Retention rules

### Active operational thread

Stores at minimum:

- provider, project, environment, service, operation
- preflight_job_id, execution_job_id
- approved_at, status, last_evidence, last_logs, last_verified_at
- failure_reason when present

### Expired thread behavior

Expiration reduces confidence in *active thread freshness* — not permission to forget recent jobs or topology.

When a thread expires, AethOS should:

1. Attempt job-led reconstruction
2. Attempt topology-led reconstruction for named services
3. Only then ask a targeted clarification question

## Readonly vs mutating memory use

- **Readonly requests** (logs, status, timestamps, verification readbacks) may proceed from topology + inventory without an active mutation thread.
- **Mutating requests** require governed preflight, approval, and execution job truth.

## Memory retrieval policy

Memory retrieval is **semantic and continuity-aware**.

Recent operational investigations outrank generic topology reconstruction.

The system must prefer:

1. active investigation continuity
2. recent operational timeline
3. semantic service match
4. topology reconstruction
5. generic provider inventory

**Expired thread ≠ forgotten operation.**

Job truth, timeline entries, and operational focus persist beyond thread TTL.

- Generic fallback when a known service, job ID, or operational keyword is present
- Passive "tell me what you need" during reconstructable operational follow-up
- Treating job lifecycle `completed` as operational thread amnesia
- Answering from stale memory when fresh job evidence exists
