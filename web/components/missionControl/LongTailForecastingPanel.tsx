"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAutonomousStability,
  fetchForecastingMemory,
  fetchLongTailForecastingState,
  fetchOperationalSurvivability,
  fetchReplayLongevity,
  fetchRealityHarnessV45,
  fetchResilienceExhaustion,
  fetchTopologySustainability,
  type LongTailForecastingState,
} from "@/lib/missionControl/longTailForecastingApi";

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
  "ltf-long-tail-forecasting": "Long-Tail Forecasting",
  "ltf-operational-survivability": "Operational Survivability",
  "ltf-replay-longevity": "Replay Longevity",
  "ltf-topology-sustainability": "Topology Sustainability",
  "ltf-resilience-exhaustion": "Resilience Exhaustion",
  "ltf-stability-endurance": "Stability Endurance",
  "ltf-autonomous-stability": "Autonomous Stability",
  "ltf-forecasting-trajectories": "Forecasting Trajectories",
  "ltf-forecasting-memory": "Long-Tail Operational Memory",
};

export function LongTailForecastingPanel({ view }: Props) {
  const [state, setState] = useState<LongTailForecastingState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "ltf-operational-survivability") {
        const survivability = await fetchOperationalSurvivability();
        setState({ ok: true, phase: "11.4.7", operational_survivability: survivability });
      } else if (view === "ltf-replay-longevity") {
        const replay = await fetchReplayLongevity();
        setState({ ok: true, phase: "11.4.7", replay_longevity_forecasting: replay });
      } else if (view === "ltf-topology-sustainability") {
        const topology = await fetchTopologySustainability();
        setState({ ok: true, phase: "11.4.7", topology_sustainability: topology });
      } else if (view === "ltf-resilience-exhaustion") {
        const exhaustion = await fetchResilienceExhaustion();
        setState({ ok: true, phase: "11.4.7", resilience_exhaustion: exhaustion });
      } else if (view === "ltf-stability-endurance" || view === "ltf-autonomous-stability") {
        const stability = await fetchAutonomousStability();
        setState({ ok: true, phase: "11.4.7", autonomous_stability: stability });
      } else if (view === "ltf-forecasting-memory") {
        await fetchForecastingMemory();
        setState(await fetchLongTailForecastingState());
      } else {
        const full = await fetchLongTailForecastingState();
        if (view === "ltf-long-tail-forecasting" || view === "ltf-forecasting-trajectories") {
          const harness = await fetchRealityHarnessV45();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load long-tail forecasting");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const forecasting = state?.long_tail_forecasting;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Long-Tail Forecasting"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Long-tail operational forecasting — survivability trajectories, replay longevity, and autonomous stability cognition.
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
            {state.converged ? "Long-tail qualified" : "Long-tail monitoring"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {(view === "ltf-long-tail-forecasting" || view === "ltf-forecasting-trajectories") && forecasting ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{forecasting.summary}</p>
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

      {view === "ltf-operational-survivability" && state?.operational_survivability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_survivability.summary}</p></div>
      ) : null}

      {view === "ltf-replay-longevity" && state?.replay_longevity_forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_longevity_forecasting.summary}</p></div>
      ) : null}

      {view === "ltf-topology-sustainability" && state?.topology_sustainability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.topology_sustainability.summary}</p></div>
      ) : null}

      {view === "ltf-resilience-exhaustion" && state?.resilience_exhaustion?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.resilience_exhaustion.summary}</p></div>
      ) : null}

      {(view === "ltf-stability-endurance" || view === "ltf-autonomous-stability") && state?.autonomous_stability?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.autonomous_stability.summary}</p></div>
      ) : null}

      {view === "ltf-forecasting-memory" && forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{forecasting.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "ltf-long-tail-forecasting" ? (
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
