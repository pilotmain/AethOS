"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchInfrastructureIntuition,
  fetchKubernetesConvergence,
  fetchOperationalMemory,
  fetchRealityHarnessV42,
  fetchReplayContinuityIntelligence,
  fetchRuntimeConvergenceCognitionState,
  fetchTemporalConfidence,
  type RuntimeConvergenceCognitionState,
} from "@/lib/missionControl/convergenceCognitionApi";

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
  "ccg-convergence-cognition": "Convergence Cognition",
  "ccg-infrastructure-intuition": "Infrastructure Intuition",
  "ccg-temporal-confidence": "Temporal Confidence",
  "ccg-kubernetes-convergence": "Kubernetes Convergence",
  "ccg-replay-continuity": "Replay Continuity",
  "ccg-long-tail-stability": "Long-Tail Stability",
  "ccg-operational-memory": "Operational Memory",
  "ccg-runtime-trajectories": "Runtime Trajectories",
};

export function ConvergenceCognitionPanel({ view }: Props) {
  const [state, setState] = useState<RuntimeConvergenceCognitionState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "ccg-infrastructure-intuition") {
        const intuition = await fetchInfrastructureIntuition();
        setState({ ok: true, phase: "11.4.4", infrastructure_intuition: intuition });
      } else if (view === "ccg-temporal-confidence") {
        const temporal = await fetchTemporalConfidence();
        setState({ ok: true, phase: "11.4.4", temporal_confidence: temporal });
      } else if (view === "ccg-kubernetes-convergence") {
        const kubernetes = await fetchKubernetesConvergence();
        setState({ ok: true, phase: "11.4.4", kubernetes_convergence: kubernetes });
      } else if (view === "ccg-replay-continuity") {
        const replay = await fetchReplayContinuityIntelligence();
        setState({ ok: true, phase: "11.4.4", replay_continuity: replay });
      } else if (view === "ccg-operational-memory" || view === "ccg-long-tail-stability") {
        const memory = await fetchOperationalMemory();
        setState({ ok: true, phase: "11.4.4", operational_memory: memory });
      } else if (view === "ccg-runtime-trajectories") {
        const full = await fetchRuntimeConvergenceCognitionState();
        setState(full);
      } else {
        const full = await fetchRuntimeConvergenceCognitionState();
        if (view === "ccg-convergence-cognition") {
          const harness = await fetchRealityHarnessV42();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load convergence cognition");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const cognition = state?.convergence_cognition;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Convergence Cognition"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Runtime convergence cognition — operational understanding over time, not verification alone.
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
            {state.converged ? "Converged" : "Converging"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "ccg-convergence-cognition" && cognition ? (
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

      {view === "ccg-infrastructure-intuition" && state?.infrastructure_intuition?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.infrastructure_intuition.summary}</p></div>
      ) : null}

      {view === "ccg-temporal-confidence" && state?.temporal_confidence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.temporal_confidence.summary}</p></div>
      ) : null}

      {view === "ccg-kubernetes-convergence" && state?.kubernetes_convergence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.kubernetes_convergence.summary}</p></div>
      ) : null}

      {view === "ccg-replay-continuity" && state?.replay_continuity?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.replay_continuity.summary}</p></div>
      ) : null}

      {(view === "ccg-operational-memory" || view === "ccg-long-tail-stability") && state?.operational_memory?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_memory.summary}</p></div>
      ) : null}

      {view === "ccg-runtime-trajectories" && cognition?.trajectories?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{cognition.trajectories.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "ccg-convergence-cognition" ? (
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
