# Mission Control — Cross-Lane Observability (FIX 128)

**Read-only** operational visibility across governed lanes. No new mutation capability.

```text
Railway / infra  ≠  software delivery  ≠  production governance  ≠  incident command
```

---

## Features

| Feature | Command |
|---------|---------|
| Unified snapshot | `show mission control snapshot` |
| Unified timeline | `show mission control timeline` |
| Attention queue | `show mission control attention queue` |
| Health summary | `show mission control health summary` |
| Audit search | `search mission control audit <query>` |
| Dashboard alias | `show mission control dashboard` |

---

## Observed lanes

- Railway orchestration (execution journals / receipts)
- Software delivery (125A–125I gates + timeline)
- Production governance (rollout / shadow records)
- Incident command (production incidents)
- Multi-agent collaboration (FIX 127 advisory)
- Route diagnostics (last route trace)
- Durable job graph (registry)

---

## Outputs

- `correlation_id` — cross-lane session correlation
- `attention_queue` — pending governance gates
- `execution_health` — summary posture
- `unified_timeline` — merged recent events

---

## Contract

`aethos_core/mission_control/cross_lane/cross_lane_contract.py`
