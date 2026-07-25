"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAdaptiveRuntimeVerification,
  fetchInfrastructureConvergence,
  fetchLongTailStability,
  fetchRecoveryContinuityIntelligenceState,
  fetchRecoveryMemory,
  fetchReplayPersistence,
  fetchRealityHarnessV42Recovery,
  fetchTemporalOperationalTrust,
  fetchTopologyResilience,
  type RecoveryContinuityIntelligenceState,
} from "@/lib/missionControl/recoveryContinuityApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const titles: Record<string, string> = {
  "rci-recovery-continuity": "Recovery Continuity",
  "rci-temporal-trust": "Temporal Trust",
  "rci-infrastructure-convergence": "Infrastructure Convergence",
  "rci-replay-persistence": "Replay Persistence",
  "rci-adaptive-verification": "Adaptive Verification",
  "rci-long-tail-stability": "Long-Tail Stability",
  "rci-topology-resilience": "Topology Resilience",
  "rci-recovery-memory": "Recovery Memory",
};

export function RecoveryContinuityPanel({ view }: Props) {
  const [state, setState] = useState<RecoveryContinuityIntelligenceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "rci-temporal-trust") {
        const trust = await fetchTemporalOperationalTrust();
        setState({ ok: true, phase: "11.6.2", temporal_operational_trust: trust });
      } else if (view === "rci-infrastructure-convergence") {
        const infra = await fetchInfrastructureConvergence();
        setState({ ok: true, phase: "11.6.2", infrastructure_convergence: infra });
      } else if (view === "rci-replay-persistence") {
        const replay = await fetchReplayPersistence();
        setState({ ok: true, phase: "11.6.2", replay_persistence: replay });
      } else if (view === "rci-adaptive-verification") {
        const adaptive = await fetchAdaptiveRuntimeVerification();
        setState({ ok: true, phase: "11.6.2", adaptive_runtime_verification: adaptive });
      } else if (view === "rci-long-tail-stability") {
        const stability = await fetchLongTailStability();
        setState({ ok: true, phase: "11.6.2", long_tail_stability: stability });
      } else if (view === "rci-topology-resilience") {
        const resilience = await fetchTopologyResilience();
        setState({
          ok: true,
          phase: "11.6.2",
          infrastructure_convergence: { topology_resilience: resilience, summary: resilience.summary },
        });
      } else if (view === "rci-recovery-memory") {
        await fetchRecoveryMemory();
        const full = await fetchRecoveryContinuityIntelligenceState();
        setState(full);
      } else {
        const full = await fetchRecoveryContinuityIntelligenceState();
        if (view === "rci-recovery-continuity") {
          const harness = await fetchRealityHarnessV42Recovery();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load recovery continuity intelligence");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const continuity = state?.recovery_continuity;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Recovery Continuity"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Recovery continuity cognition — operational trust earned when systems remain stable through evolving conditions.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.phase ? (
        <div style={cardStyle}>
          <span style={{ color: state.converged ? mcColors.green : mcColors.cyan, fontWeight: 600 }}>
            {state.converged ? "Continuity established" : "Continuity converging"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "rci-recovery-continuity" && continuity ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{continuity.summary}</p>
            {state?.narrative ? <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>{state.narrative}</p> : null}
          </div>
          {state?.harness ? (
            <div style={cardStyle}>
              <span style={{ fontWeight: 600 }}>Harness {state.harness.harness_version}</span>
              <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
                {state.harness.verified_count}/{state.harness.scenario_count} verified
              </p>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "rci-temporal-trust" && state?.temporal_operational_trust?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.temporal_operational_trust.summary}</p></div>
      ) : null}

      {view === "rci-infrastructure-convergence" && state?.infrastructure_convergence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.infrastructure_convergence.summary}</p></div>
      ) : null}

      {view === "rci-replay-persistence" && state?.replay_persistence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_persistence.summary}</p></div>
      ) : null}

      {view === "rci-adaptive-verification" && state?.adaptive_runtime_verification?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.adaptive_runtime_verification.summary}</p></div>
      ) : null}

      {view === "rci-long-tail-stability" && state?.long_tail_stability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.long_tail_stability.summary}</p></div>
      ) : null}

      {view === "rci-topology-resilience" && state?.infrastructure_convergence?.topology_resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.infrastructure_convergence.topology_resilience.summary}</p></div>
      ) : null}

      {view === "rci-recovery-memory" && continuity?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{continuity.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "rci-recovery-continuity" ? (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Strategic position</span>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: mcColors.textMuted }}>
            {Object.entries(state.strategic_position).map(([key, value]) => (
              <li key={key}>{key.replace(/_/g, " ")}: {value}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
