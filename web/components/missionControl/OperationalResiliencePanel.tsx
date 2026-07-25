"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchKubernetesRuntimeDurability,
  fetchOperationalRecoveryDurability,
  fetchOperationalResilienceLongTail,
  fetchOperationalResilienceMemory,
  fetchOperationalResilienceState,
  fetchReplayResilienceCognition,
  fetchRealityHarnessV43Operational,
  fetchRuntimeFragility,
  fetchSustainedTrustEvolution,
  type OperationalResilienceState,
} from "@/lib/missionControl/operationalResilienceApi";

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
  "ors-operational-resilience": "Operational Resilience",
  "ors-runtime-fragility": "Runtime Fragility",
  "ors-sustained-trust": "Sustained Trust",
  "ors-kubernetes-durability": "Kubernetes Durability",
  "ors-replay-resilience": "Replay Resilience",
  "ors-long-tail-stability": "Long-Tail Stability",
  "ors-recovery-durability": "Recovery Durability",
  "ors-operational-trajectories": "Operational Trajectories",
};

export function OperationalResiliencePanel({ view }: Props) {
  const [state, setState] = useState<OperationalResilienceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "ors-runtime-fragility") {
        const fragility = await fetchRuntimeFragility();
        setState({ ok: true, phase: "11.6.3", runtime_fragility: fragility });
      } else if (view === "ors-sustained-trust") {
        const trust = await fetchSustainedTrustEvolution();
        setState({ ok: true, phase: "11.6.3", sustained_trust_evolution: trust });
      } else if (view === "ors-kubernetes-durability") {
        const k8s = await fetchKubernetesRuntimeDurability();
        setState({ ok: true, phase: "11.6.3", kubernetes_durability: k8s });
      } else if (view === "ors-replay-resilience") {
        const replay = await fetchReplayResilienceCognition();
        setState({ ok: true, phase: "11.6.3", replay_resilience: replay });
      } else if (view === "ors-long-tail-stability") {
        const stability = await fetchOperationalResilienceLongTail();
        setState({ ok: true, phase: "11.6.3", summary: stability.summary });
      } else if (view === "ors-recovery-durability") {
        const durability = await fetchOperationalRecoveryDurability();
        setState({ ok: true, phase: "11.6.3", operational_resilience: { trajectories: durability, summary: durability.summary } });
      } else if (view === "ors-operational-trajectories") {
        setState(await fetchOperationalResilienceState());
      } else {
        const full = await fetchOperationalResilienceState();
        if (view === "ors-operational-resilience") {
          const harness = await fetchRealityHarnessV43Operational();
          const memory = await fetchOperationalResilienceMemory();
          setState({ ...full, harness: harness ?? full.harness, long_tail_resilience: memory ?? full.long_tail_resilience });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load operational resilience");
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
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Operational Resilience"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Phase 11.6.3 — resilience-aware operational cognition under sustained runtime pressure.
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

      {view === "ors-operational-resilience" && resilience ? (
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

      {view === "ors-runtime-fragility" && state?.runtime_fragility?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.runtime_fragility.summary}</p></div>
      ) : null}

      {view === "ors-sustained-trust" && state?.sustained_trust_evolution?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.sustained_trust_evolution.summary}</p></div>
      ) : null}

      {view === "ors-kubernetes-durability" && state?.kubernetes_durability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.kubernetes_durability.summary}</p></div>
      ) : null}

      {view === "ors-replay-resilience" && state?.replay_resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_resilience.summary}</p></div>
      ) : null}

      {view === "ors-long-tail-stability" && state?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.summary}</p></div>
      ) : null}

      {view === "ors-recovery-durability" && resilience?.trajectories?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{resilience.trajectories.summary}</p></div>
      ) : null}

      {view === "ors-operational-trajectories" && resilience?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{resilience.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "ors-operational-resilience" ? (
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
