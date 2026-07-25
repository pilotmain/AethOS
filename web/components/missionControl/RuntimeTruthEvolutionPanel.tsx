"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAdaptiveVerification,
  fetchLongTailDecay,
  fetchRecoveryConvergence,
  fetchRealityHarnessV41,
  fetchRuntimeTruthConvergenceState,
  fetchStabilityWindows,
  type RuntimeTruthConvergenceState,
} from "@/lib/missionControl/runtimeTruthConvergenceApi";

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
  "rtc-runtime-truth": "Runtime Truth",
  "rtc-stability-windows": "Stability Windows",
  "rtc-replay-convergence": "Replay Convergence",
  "rtc-dependency-stability": "Dependency Stability",
  "rtc-topology-truth": "Topology Truth",
  "rtc-operational-decay": "Operational Decay",
  "rtc-sustained-confidence": "Sustained Confidence",
  "rtc-recovery-continuity": "Recovery Continuity",
};

export function RuntimeTruthEvolutionPanel({ view }: Props) {
  const [state, setState] = useState<RuntimeTruthConvergenceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "rtc-stability-windows") {
        const windows = await fetchStabilityWindows();
        setState({ ok: true, phase: "11.6.1", stability_windows: windows });
      } else if (view === "rtc-replay-convergence" || view === "rtc-topology-truth" || view === "rtc-dependency-stability") {
        setState(await fetchRuntimeTruthConvergenceState());
      } else if (view === "rtc-recovery-continuity") {
        const recovery = await fetchRecoveryConvergence();
        setState({ ok: true, phase: "11.6.1", recovery_convergence: recovery });
      } else if (view === "rtc-operational-decay") {
        const decay = await fetchLongTailDecay();
        setState({ ok: true, phase: "11.6.1", long_tail_decay: decay });
      } else if (view === "rtc-sustained-confidence") {
        const adaptive = await fetchAdaptiveVerification();
        setState({ ok: true, phase: "11.6.1", adaptive_verification: adaptive });
      } else {
        const full = await fetchRuntimeTruthConvergenceState();
        if (view === "rtc-runtime-truth") {
          const harness = await fetchRealityHarnessV41();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runtime truth convergence");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const rt = state?.runtime_truth;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Runtime Truth Evolution"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Continuously converging operational truth — sustained verification, replay continuity, and long-tail stabilization.
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

      {view === "rtc-runtime-truth" && rt ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{rt.summary}</p>
            {rt.narrative ? <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>{rt.narrative}</p> : null}
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

      {view === "rtc-stability-windows" && state?.stability_windows?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.stability_windows.summary}</p></div>
      ) : null}

      {view === "rtc-replay-convergence" && rt?.replay_truth?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{rt.replay_truth.summary}</p></div>
      ) : null}

      {view === "rtc-dependency-stability" && state?.recovery_convergence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.recovery_convergence.summary}</p></div>
      ) : null}

      {view === "rtc-topology-truth" && rt?.topology_truth?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{rt.topology_truth.summary}</p></div>
      ) : null}

      {view === "rtc-operational-decay" && state?.long_tail_decay?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.long_tail_decay.summary}</p></div>
      ) : null}

      {view === "rtc-sustained-confidence" && state?.adaptive_verification?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.adaptive_verification.summary}</p></div>
      ) : null}

      {view === "rtc-recovery-continuity" && state?.recovery_convergence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.recovery_convergence.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "rtc-runtime-truth" ? (
        Object.entries(state.strategic_position).map(([key, val]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: mcColors.cyan }}>{val}</span>
          </div>
        ))
      ) : null}
    </div>
  );
}
