"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchFragilityAcceleration,
  fetchOperationalFatigue,
  fetchPredictiveMemory,
  fetchPredictiveOperationalCognitionState,
  fetchRecoveryForecasting,
  fetchReplayForecasting,
  fetchRealityHarnessV44,
  fetchStabilityProjection,
  fetchTopologyForecasting,
  type PredictiveOperationalCognitionState,
} from "@/lib/missionControl/predictiveCognitionApi";

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
  "poc-predictive-stability": "Predictive Stability",
  "poc-fragility-acceleration": "Fragility Acceleration",
  "poc-replay-forecasting": "Replay Forecasting",
  "poc-topology-forecasting": "Topology Forecasting",
  "poc-operational-fatigue": "Operational Fatigue",
  "poc-stability-projection": "Stability Projection",
  "poc-recovery-forecasting": "Recovery Forecasting",
  "poc-predictive-memory": "Predictive Operational Memory",
};

export function PredictiveCognitionPanel({ view }: Props) {
  const [state, setState] = useState<PredictiveOperationalCognitionState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "poc-fragility-acceleration") {
        const acceleration = await fetchFragilityAcceleration();
        setState({ ok: true, phase: "11.4.6", fragility_acceleration: acceleration });
      } else if (view === "poc-replay-forecasting") {
        const replay = await fetchReplayForecasting();
        setState({ ok: true, phase: "11.4.6", replay_erosion_forecasting: replay });
      } else if (view === "poc-topology-forecasting") {
        const topology = await fetchTopologyForecasting();
        setState({ ok: true, phase: "11.4.6", topology_stability_forecasting: topology });
      } else if (view === "poc-operational-fatigue") {
        const fatigue = await fetchOperationalFatigue();
        setState({ ok: true, phase: "11.4.6", operational_fatigue: fatigue });
      } else if (view === "poc-stability-projection") {
        const projection = await fetchStabilityProjection();
        setState({ ok: true, phase: "11.4.6", sustained_stability_forecasting: projection });
      } else if (view === "poc-recovery-forecasting") {
        const recovery = await fetchRecoveryForecasting();
        setState({ ok: true, phase: "11.4.6", predictive_cognition: { summary: recovery.summary } });
      } else if (view === "poc-predictive-memory") {
        await fetchPredictiveMemory();
        setState(await fetchPredictiveOperationalCognitionState());
      } else {
        const full = await fetchPredictiveOperationalCognitionState();
        if (view === "poc-predictive-stability") {
          const harness = await fetchRealityHarnessV44();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load predictive cognition");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const predictive = state?.predictive_cognition;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Predictive Cognition"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Predictive operational cognition — forecasting instability, fragility escalation, and long-tail decay trajectories.
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
            {state.converged ? "Predictively qualified" : "Predictive monitoring"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "poc-predictive-stability" && predictive ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{predictive.summary}</p>
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

      {view === "poc-fragility-acceleration" && state?.fragility_acceleration?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.fragility_acceleration.summary}</p></div>
      ) : null}

      {view === "poc-replay-forecasting" && state?.replay_erosion_forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_erosion_forecasting.summary}</p></div>
      ) : null}

      {view === "poc-topology-forecasting" && state?.topology_stability_forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.topology_stability_forecasting.summary}</p></div>
      ) : null}

      {view === "poc-operational-fatigue" && state?.operational_fatigue?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_fatigue.summary}</p></div>
      ) : null}

      {view === "poc-stability-projection" && state?.sustained_stability_forecasting?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.sustained_stability_forecasting.summary}</p></div>
      ) : null}

      {view === "poc-recovery-forecasting" && predictive?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{predictive.summary}</p></div>
      ) : null}

      {view === "poc-predictive-memory" && predictive?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{predictive.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "poc-predictive-stability" ? (
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
