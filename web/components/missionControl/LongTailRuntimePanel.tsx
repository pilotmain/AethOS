"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchCognitionMemory,
  fetchLongTailRuntimeCognitionState,
  fetchOperationalEndurance,
  fetchReplayContinuity,
  fetchRealityHarnessV45Runtime,
  fetchResilienceExhaustionIntelligence,
  fetchRuntimeSurvivability,
  fetchTopologyEndurance,
  type LongTailRuntimeCognitionState,
} from "@/lib/missionControl/longTailRuntimeApi";

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
  "ltr-long-tail-cognition": "Long-Tail Cognition",
  "ltr-runtime-survivability": "Runtime Survivability",
  "ltr-operational-endurance": "Operational Endurance",
  "ltr-replay-continuity": "Replay Continuity",
  "ltr-topology-endurance": "Topology Endurance",
  "ltr-resilience-exhaustion": "Resilience Exhaustion",
  "ltr-runtime-persistence": "Runtime Persistence",
  "ltr-cognition-memory": "Cognition Memory",
};

export function LongTailRuntimePanel({ view }: Props) {
  const [state, setState] = useState<LongTailRuntimeCognitionState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "ltr-runtime-survivability") {
        const survivability = await fetchRuntimeSurvivability();
        setState({ ok: true, phase: "11.6.5", runtime_survivability_intelligence: survivability });
      } else if (view === "ltr-operational-endurance" || view === "ltr-runtime-persistence") {
        const endurance = await fetchOperationalEndurance();
        setState({ ok: true, phase: "11.6.5", operational_endurance: endurance });
      } else if (view === "ltr-replay-continuity") {
        const replay = await fetchReplayContinuity();
        setState({ ok: true, phase: "11.6.5", replay_continuity_survivability: replay });
      } else if (view === "ltr-topology-endurance") {
        const topology = await fetchTopologyEndurance();
        setState({ ok: true, phase: "11.6.5", topology_endurance_forecasting: topology });
      } else if (view === "ltr-resilience-exhaustion") {
        const exhaustion = await fetchResilienceExhaustionIntelligence();
        setState({ ok: true, phase: "11.6.5", resilience_exhaustion_intelligence: exhaustion });
      } else if (view === "ltr-cognition-memory") {
        await fetchCognitionMemory();
        setState(await fetchLongTailRuntimeCognitionState());
      } else {
        const full = await fetchLongTailRuntimeCognitionState();
        if (view === "ltr-long-tail-cognition") {
          const harness = await fetchRealityHarnessV45Runtime();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load long-tail runtime cognition");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const cognition = state?.long_tail_runtime_cognition;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Long-Tail Runtime Cognition"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Long-tail runtime cognition — survivability intelligence, operational endurance, and replay continuity persistence.
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
            {state.converged ? "Runtime survivability qualified" : "Long-tail monitoring"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "ltr-long-tail-cognition" && cognition ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{cognition.summary}</p>
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

      {view === "ltr-runtime-survivability" && state?.runtime_survivability_intelligence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.runtime_survivability_intelligence.summary}</p></div>
      ) : null}

      {(view === "ltr-operational-endurance" || view === "ltr-runtime-persistence") && state?.operational_endurance?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_endurance.summary}</p></div>
      ) : null}

      {view === "ltr-replay-continuity" && state?.replay_continuity_survivability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_continuity_survivability.summary}</p></div>
      ) : null}

      {view === "ltr-topology-endurance" && state?.topology_endurance_forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.topology_endurance_forecasting.summary}</p></div>
      ) : null}

      {view === "ltr-resilience-exhaustion" && state?.resilience_exhaustion_intelligence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.resilience_exhaustion_intelligence.summary}</p></div>
      ) : null}

      {view === "ltr-cognition-memory" && cognition?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{cognition.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "ltr-long-tail-cognition" ? (
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
