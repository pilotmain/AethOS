"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchOperationalPatience,
  fetchRecoveryTruth,
  fetchRuntimeDecay,
  fetchRuntimeReconciliationState,
  fetchRealityHarnessV41,
  fetchVerificationWindows,
  type RuntimeTruthState,
} from "@/lib/missionControl/runtimeTruthApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const statusColor = (ok?: boolean) => (ok ? mcColors.green : mcColors.cyan);

const titles: Record<string, string> = {
  "rt-reconciliation": "Runtime Reconciliation",
  "rt-operational-patience": "Operational Patience",
  "rt-runtime-decay": "Runtime Decay",
  "rt-sustained-verification": "Sustained Verification",
  "rt-recovery-truth": "Recovery Truth",
  "rt-replay-stability": "Replay Stability",
  "rt-topology-alignment": "Topology Alignment",
  "rt-operational-windows": "Operational Windows",
};

export function RuntimeTruthPanel({ view }: Props) {
  const [state, setState] = useState<RuntimeTruthState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "rt-operational-patience") {
        const patience = await fetchOperationalPatience();
        setState({ ok: true, phase: "11.4.3", operational_patience: patience });
      } else if (view === "rt-runtime-decay") {
        const decay = await fetchRuntimeDecay();
        setState({ ok: true, phase: "11.4.3", runtime_decay: decay });
      } else if (view === "rt-sustained-verification" || view === "rt-operational-windows") {
        const windows = await fetchVerificationWindows();
        setState({ ok: true, phase: "11.4.3", verification_windows: windows });
      } else if (view === "rt-recovery-truth") {
        const recovery = await fetchRecoveryTruth();
        setState({ ok: true, phase: "11.4.3", recovery_truth: recovery });
      } else {
        const full = await fetchRuntimeReconciliationState();
        if (view === "rt-replay-stability" || view === "rt-topology-alignment") {
          setState(full);
        } else {
          const harness = view === "rt-reconciliation" ? await fetchRealityHarnessV41() : null;
          setState(harness ? { ...full, harness } : full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runtime truth");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Runtime Truth"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Continuous operational reconciliation — runtime patience, decay awareness, and sustained execution truth.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.phase ? (
        <div style={cardStyle}>
          <span style={{ color: statusColor(state.converged), fontWeight: 600 }}>
            {state.converged ? "Converged" : "Reconciling"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "rt-reconciliation" && state?.reconciliation ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.reconciliation.summary}</p>
            {state.reconciliation.narrative ? (
              <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>{state.reconciliation.narrative}</p>
            ) : null}
          </div>
          {state.harness ? (
            <div style={cardStyle}>
              <span style={{ fontWeight: 600 }}>Harness {state.harness.harness_version}</span>
              <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
                {state.harness.verified_count}/{state.harness.scenario_count} verified
              </p>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "rt-operational-patience" && state?.operational_patience?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_patience.summary}</p>
        </div>
      ) : null}

      {view === "rt-runtime-decay" && state?.runtime_decay?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.runtime_decay.summary}</p>
        </div>
      ) : null}

      {view === "rt-sustained-verification" && state?.verification_windows?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.verification_windows.summary}</p>
        </div>
      ) : null}

      {view === "rt-recovery-truth" && state?.recovery_truth?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.recovery_truth.summary}</p>
        </div>
      ) : null}

      {view === "rt-replay-stability" && state?.reconciliation?.replay_alignment?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.reconciliation.replay_alignment.summary}</p>
        </div>
      ) : null}

      {view === "rt-topology-alignment" && state?.reconciliation?.topology_alignment?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.reconciliation.topology_alignment.summary}</p>
        </div>
      ) : null}

      {view === "rt-operational-windows" && state?.verification_windows?.verification_windows?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            {state.verification_windows.verification_windows.summary}
          </p>
        </div>
      ) : null}

      {state?.strategic_position && view === "rt-reconciliation" ? (
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
