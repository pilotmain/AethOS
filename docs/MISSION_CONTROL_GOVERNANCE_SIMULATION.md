# FIX 144 — Governance Simulation Sandbox

**Governance experimentation without governance mutation** — simulate hypothetical policy configurations and compare impacts.

## Invariant

```text
governance_simulation → baseline from FIX 143 signals → hypothetical scenarios → impact estimates
NO live policy mutation · NO auto-policy updates · NO automatic governance tuning
```

## Scenarios (catalog)

| ID | Simulates |
|----|-----------|
| `alternate_approval_chain` | Verification-first gate sequencing |
| `reduced_quorum` | Fewer approval touches (higher risk estimate) |
| `increased_quorum` | Dual approval on push/open gates |
| `strict_rollout_policy` | Zero open incidents before rollout thinking |
| `stricter_verification` | Double workspace_verify weight |
| `alternate_gate_sequencing` | Reversed patch/apply order |

## Estimated impacts (per scenario)

- Governance friction index (baseline vs simulated, Δ)
- Mission latency hours (estimate)
- Risk exposure (label + score delta)

Plus **side-by-side comparison** table across all scenarios.

All results: `executable: false`, `applied_to_live_policy: false`.

## Chat

```text
run governance simulation
compare governance configurations
governance sandbox
simulate increased quorum
```

Rejected: `apply simulation to live policy`, `auto-tune policy`.

## API

```http
GET /api/v1/mission-control/governance-simulation?session_id=<session>&scenarios=all|<comma_ids>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Governance simulation**

## Tests

```bash
pytest tests/test_mission_control_governance_simulation.py -q
```

## Related (FIX 145)

Mission strategy composes simulation and insights into long-horizon strategic reasoning. See [MISSION_CONTROL_MISSION_STRATEGY.md](./MISSION_CONTROL_MISSION_STRATEGY.md).
