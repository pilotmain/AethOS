"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchDegradationAcceleration,
  fetchFragilityMemory,
  fetchOperationalFatigueCognition,
  fetchPredictiveRuntimeStability,
  fetchRecoveryFragility,
  fetchReplayErosionIntelligence,
  fetchRuntimeFragilityIntelligenceState,
  fetchRealityHarnessV44Fragility,
  fetchTopologyFragilityForecasting,
  type RuntimeFragilityIntelligenceState,
} from "@/lib/missionControl/runtimeFragilityApi";

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
  "rfi-runtime-fragility": "Runtime Fragility",
  "rfi-degradation-acceleration": "Degradation Acceleration",
  "rfi-replay-erosion": "Replay Erosion",
  "rfi-topology-fragility": "Topology Fragility",
  "rfi-operational-fatigue": "Operational Fatigue",
  "rfi-predictive-stability": "Predictive Stability",
  "rfi-recovery-fragility": "Recovery Fragility",
  "rfi-fragility-memory": "Fragility Memory",
};

export function RuntimeFragilityPanel({ view }: Props) {
  const [state, setState] = useState<RuntimeFragilityIntelligenceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "rfi-degradation-acceleration") {
        const acceleration = await fetchDegradationAcceleration();
        setState({ ok: true, phase: "11.6.4", degradation_acceleration: acceleration });
      } else if (view === "rfi-replay-erosion") {
        const replay = await fetchReplayErosionIntelligence();
        setState({ ok: true, phase: "11.6.4", replay_erosion: replay });
      } else if (view === "rfi-topology-fragility") {
        const topology = await fetchTopologyFragilityForecasting();
        setState({ ok: true, phase: "11.6.4", topology_fragility: topology });
      } else if (view === "rfi-operational-fatigue") {
        const fatigue = await fetchOperationalFatigueCognition();
        setState({ ok: true, phase: "11.6.4", operational_fatigue: fatigue });
      } else if (view === "rfi-predictive-stability") {
        const predictive = await fetchPredictiveRuntimeStability();
        setState({ ok: true, phase: "11.6.4", predictive_stability: predictive });
      } else if (view === "rfi-recovery-fragility") {
        const recovery = await fetchRecoveryFragility();
        setState({ ok: true, phase: "11.6.4", degradation_acceleration: recovery });
      } else if (view === "rfi-fragility-memory") {
        await fetchFragilityMemory();
        setState(await fetchRuntimeFragilityIntelligenceState());
      } else {
        const full = await fetchRuntimeFragilityIntelligenceState();
        if (view === "rfi-runtime-fragility") {
          const harness = await fetchRealityHarnessV44Fragility();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runtime fragility intelligence");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const fragility = state?.runtime_fragility;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Runtime Fragility"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Phase 11.6.4 — predictive runtime fragility intelligence before visible operational failure.
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
            {state.converged ? "Fragility bounded" : "Fragility monitoring"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "rfi-runtime-fragility" && fragility ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{fragility.summary}</p>
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

      {view === "rfi-degradation-acceleration" && state?.degradation_acceleration?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.degradation_acceleration.summary}</p></div>
      ) : null}

      {view === "rfi-replay-erosion" && state?.replay_erosion?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_erosion.summary}</p></div>
      ) : null}

      {view === "rfi-topology-fragility" && state?.topology_fragility?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.topology_fragility.summary}</p></div>
      ) : null}

      {view === "rfi-operational-fatigue" && state?.operational_fatigue?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_fatigue.summary}</p></div>
      ) : null}

      {view === "rfi-predictive-stability" && state?.predictive_stability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.predictive_stability.summary}</p></div>
      ) : null}

      {view === "rfi-recovery-fragility" && state?.degradation_acceleration?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.degradation_acceleration.summary}</p></div>
      ) : null}

      {view === "rfi-fragility-memory" && fragility?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{fragility.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "rfi-runtime-fragility" ? (
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
