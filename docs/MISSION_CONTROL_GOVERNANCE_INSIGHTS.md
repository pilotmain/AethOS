# FIX 143 — Adaptive Governance Insights (meta-governance, read-only)

**Meta-governance observability** — AethOS understanding how its own governance system behaves over time.

## Invariant

```text
governance_insights → audit + memory + rollouts + rollbacks + cross-session signals
→ meta-governance analysis (insight-only)
NO policy auto-tuning · NO governance self-modification · NO autonomous optimization
```

## Insight sections

| Section | Detects |
|---------|---------|
| Approval bottlenecks | High-frequency gates, pending inbox depth |
| Governance friction | Cross-session blockers, view-only gates |
| Rollback patterns | Production rollback escalation journal |
| Verification gaps | Gates without verification graph nodes |
| Approval-chain inefficiencies | Negative outcome skew, repeated gate loops |
| High-risk rollout sequences | Risky stages + open incidents |
| Governance health metrics | Heuristic health score + telemetry counts |
| Operator workload heatmap | Approval audit load by session |
| Mission completion latency | Plan snapshot span (hours) |

All insights: `executable: false`, `read_only: true`.

## Chat

```text
show governance insights
meta-governance health
governance telemetry
approval bottlenecks
```

Rejected: `auto-tune policy`, `modify governance`, `self-modifying governance`.

## API

```http
GET /api/v1/mission-control/governance-insights?session_id=<session>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Governance insights**

## Tests

```bash
pytest tests/test_mission_control_governance_insights.py -q
```

## Related (FIX 144)

Governance simulation sandbox experiments with hypothetical configurations without applying them. See [MISSION_CONTROL_GOVERNANCE_SIMULATION.md](./MISSION_CONTROL_GOVERNANCE_SIMULATION.md).
