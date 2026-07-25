"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchProductionExecutionTruthInfrastructure,
  fetchProductionExecutionTruthProviders,
  fetchProductionExecutionTruthRollback,
  fetchProductionExecutionTruthStabilization,
  fetchProductionExecutionTruthState,
  fetchProductionExecutionTruthSustainedVerification,
  fetchRealityHarnessV4,
  type ProductionExecutionTruthState,
} from "@/lib/missionControl/productionExecutionTruthApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const tierColor = (tier?: string) => {
  if (tier === "operationally-trusted" || tier === "production-reliable" || tier === "strong") return mcColors.green;
  if (tier === "stable" || tier === "converging" || tier === "emerging") return mcColors.cyan;
  return mcColors.amber;
};

const titles: Record<string, string> = {
  "prod-deployment-truth": "Deployment Truth",
  "prod-rollback-integrity": "Rollback Integrity",
  "prod-runtime-stabilization": "Runtime Stabilization",
  "prod-topology-recovery": "Topology Recovery",
  "prod-operational-decay": "Operational Decay",
  "prod-production-qualification": "Production Qualification",
  "prod-sustained-verification": "Sustained Verification",
  "prod-recovery-confidence": "Recovery Confidence",
};

export function ProductionRealityPanel({ view }: Props) {
  const [state, setState] = useState<ProductionExecutionTruthState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "prod-topology-recovery") {
        const providers = await fetchProductionExecutionTruthProviders();
        setState({ ok: true, phase: "11.6", provider_truth: providers });
      } else if (view === "prod-rollback-integrity") {
        const rollback = await fetchProductionExecutionTruthRollback();
        setState({ ok: true, phase: "11.6", rollback_integrity: rollback });
      } else if (view === "prod-runtime-stabilization") {
        const stabilization = await fetchProductionExecutionTruthStabilization();
        setState({ ok: true, phase: "11.6", runtime_stabilization: stabilization });
      } else if (view === "prod-sustained-verification") {
        const sustained = await fetchProductionExecutionTruthSustainedVerification();
        setState({ ok: true, phase: "11.6", sustained_verification: sustained });
      } else if (view === "prod-operational-decay") {
        const infra = await fetchProductionExecutionTruthInfrastructure();
        setState({ ok: true, phase: "11.6", infrastructure_truth: infra });
      } else {
        const full = await fetchProductionExecutionTruthState();
        if (view === "prod-recovery-confidence") {
          const harness = await fetchRealityHarnessV4();
          setState({ ...full, harness: harness ?? full.harness });
        } else {
          setState(full);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load production execution truth");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const checks = state?.production_qualification?.checks;
  const sustained = state?.sustained_verification;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Production Reality"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Production execution realism — runtime truth, sustained verification, and long-tail operational convergence.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.qualification_tier && view !== "prod-production-qualification" ? (
        <div style={cardStyle}>
          <span style={{ color: tierColor(state.qualification_tier), fontWeight: 600 }}>
            {state.converged ? "Converged" : "Converging"} — {state.qualification_tier}
          </span>
          {state.phase ? <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.textDim }}>Phase {state.phase}</p> : null}
        </div>
      ) : null}

      {view === "prod-deployment-truth" && state?.execution_truth?.convergence ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.execution_truth.convergence.summary}</p>
          {state.execution_truth.convergence.narrative ? (
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>{state.execution_truth.convergence.narrative}</p>
          ) : null}
        </div>
      ) : null}

      {view === "prod-rollback-integrity" && state?.rollback_integrity?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.rollback_integrity.summary}</p>
        </div>
      ) : null}

      {view === "prod-runtime-stabilization" && state?.runtime_stabilization?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.runtime_stabilization.summary}</p>
        </div>
      ) : null}

      {view === "prod-topology-recovery" && state?.provider_truth?.topology_recovery ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.provider_truth.topology_recovery.summary}</p>
        </div>
      ) : null}

      {view === "prod-operational-decay" && state?.infrastructure_truth?.decay ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            Confidence: {state.infrastructure_truth.decay.current_confidence ?? "—"} ·{" "}
            {state.infrastructure_truth.decay.decay_bounded ? "Decay bounded" : "Decay elevated"}
          </p>
        </div>
      ) : null}

      {view === "prod-production-qualification" && checks ? (
        Object.entries(checks).map(([key, passed]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: passed ? mcColors.green : mcColors.amber }}>{passed ? "pass" : "pending"}</span>
          </div>
        ))
      ) : null}

      {view === "prod-sustained-verification" && sustained ? (
        <>
          <div style={cardStyle}>
            <span style={{ color: tierColor(sustained.sustained_qualified ? "stable" : "emerging"), fontWeight: 600 }}>
              {sustained.sustained_qualified ? "Sustained qualified" : "Sustained verification active"}
            </span>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>{sustained.summary}</p>
          </div>
          {sustained.drift_reverification?.summary ? (
            <div style={cardStyle}>
              <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{sustained.drift_reverification.summary}</p>
            </div>
          ) : null}
          {sustained.replay_stability?.summary ? (
            <div style={cardStyle}>
              <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{sustained.replay_stability.summary}</p>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "prod-recovery-confidence" && state?.harness ? (
        <>
          <div style={cardStyle}>
            <span style={{ fontWeight: 600 }}>Harness {state.harness.harness_version}</span>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              {state.harness.verified_count}/{state.harness.scenario_count} verified · {state.harness.average_coverage_pct}% coverage
            </p>
          </div>
          {(state.harness.scenarios ?? []).map((s) => (
            <div key={s.id} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
              <span>{s.name}</span>
              <span style={{ color: s.status === "verified" ? mcColors.green : mcColors.amber }}>{s.status}</span>
            </div>
          ))}
        </>
      ) : null}

      {state?.strategic_position && view === "prod-production-qualification" ? (
        Object.entries(state.strategic_position).map(([key, val]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: tierColor(val) }}>{val}</span>
          </div>
        ))
      ) : null}
    </div>
  );
}
