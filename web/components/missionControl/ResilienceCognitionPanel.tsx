"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchInfrastructureFragility,
  fetchKubernetesResilience,
  fetchOperationalResilienceCognitionState,
  fetchRecoveryDurability,
  fetchReplayResilience,
  fetchRealityHarnessV43,
  fetchResilienceLongTailStability,
  fetchResilienceMemory,
  fetchTemporalTrustEvolution,
  type OperationalResilienceCognitionState,
} from "@/lib/missionControl/resilienceCognitionApi";

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
  "rsc-operational-resilience": "Operational Resilience",
  "rsc-infrastructure-fragility": "Infrastructure Fragility",
  "rsc-temporal-trust-evolution": "Temporal Trust Evolution",
  "rsc-kubernetes-resilience": "Kubernetes Resilience",
  "rsc-replay-resilience": "Replay Resilience",
  "rsc-long-tail-stability": "Long-Tail Stability",
  "rsc-recovery-durability": "Recovery Durability",
  "rsc-operational-trajectories": "Operational Trajectories",
};

export function ResilienceCognitionPanel({ view }: Props) {
  const [state, setState] = useState<OperationalResilienceCognitionState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "rsc-infrastructure-fragility") {
        const fragility = await fetchInfrastructureFragility();
        setState({ ok: true, phase: "11.4.5", infrastructure_fragility: fragility });
      } else if (view === "rsc-temporal-trust-evolution") {
        const trust = await fetchTemporalTrustEvolution();
        setState({ ok: true, phase: "11.4.5", temporal_trust_evolution: trust });
      } else if (view === "rsc-kubernetes-resilience") {
        const k8s = await fetchKubernetesResilience();
        setState({ ok: true, phase: "11.4.5", kubernetes_resilience: k8s });
      } else if (view === "rsc-replay-resilience") {
        const replay = await fetchReplayResilience();
        setState({ ok: true, phase: "11.4.5", replay_resilience: replay });
      } else if (view === "rsc-long-tail-stability") {
        const stability = await fetchResilienceLongTailStability();
        setState({ ok: true, phase: "11.4.5", summary: stability.summary });
      } else if (view === "rsc-recovery-durability") {
        const durability = await fetchRecoveryDurability();
        setState({ ok: true, phase: "11.4.5", operational_resilience: { trajectories: durability, summary: durability.summary } });
      } else if (view === "rsc-operational-trajectories") {
        const full = await fetchOperationalResilienceCognitionState();
        setState(full);
      } else {
        const full = await fetchOperationalResilienceCognitionState();
        if (view === "rsc-operational-resilience") {
          const harness = await fetchRealityHarnessV43();
          const memory = await fetchResilienceMemory();
          setState({ ...full, harness: harness ?? full.harness, resilience_memory: memory ?? full.resilience_memory });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load resilience cognition");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const resilience = state?.operational_resilience;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Resilience Cognition"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Resilience-aware operational cognition — trust earned when systems remain stable through evolving conditions.
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
            {state.converged ? "Resilience established" : "Resilience converging"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "rsc-operational-resilience" && resilience ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{resilience.summary}</p>
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

      {view === "rsc-infrastructure-fragility" && state?.infrastructure_fragility?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.infrastructure_fragility.summary}</p></div>
      ) : null}

      {view === "rsc-temporal-trust-evolution" && state?.temporal_trust_evolution?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.temporal_trust_evolution.summary}</p></div>
      ) : null}

      {view === "rsc-kubernetes-resilience" && state?.kubernetes_resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.kubernetes_resilience.summary}</p></div>
      ) : null}

      {view === "rsc-replay-resilience" && state?.replay_resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_resilience.summary}</p></div>
      ) : null}

      {view === "rsc-long-tail-stability" && state?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.summary}</p></div>
      ) : null}

      {view === "rsc-recovery-durability" && resilience?.trajectories?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{resilience.trajectories.summary}</p></div>
      ) : null}

      {view === "rsc-operational-trajectories" && resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{resilience.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "rsc-operational-resilience" ? (
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
