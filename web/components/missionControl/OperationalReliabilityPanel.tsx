"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchContinuousVerification,
  fetchDriftIntelligence,
  fetchOperationalReliabilityState,
  fetchPredictiveOperations,
  fetchProductionConfidence,
  fetchRecoveryOrchestration,
  fetchReliabilityHarness,
  type OperationalReliabilityState,
} from "@/lib/missionControl/operationalReliabilityApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const maturityColor = (tier?: string) => {
  if (tier === "production-reliable" || tier === "production-ready" || tier === "stable") return mcColors.green;
  if (tier === "beta") return mcColors.cyan;
  return mcColors.amber;
};

const titles: Record<string, string> = {
  "reliability-continuous-verification": "Continuous Verification",
  "reliability-recovery-orchestration": "Recovery Orchestration",
  "reliability-drift-intelligence": "Drift Intelligence",
  "reliability-predictive-operations": "Predictive Operations",
  "reliability-production-confidence": "Production Confidence",
  "reliability-reliability-memory": "Reliability Memory",
  "reliability-operational-trajectory": "Operational Trajectory",
  "reliability-confidence-forecasting": "Confidence Forecasting",
};

export function OperationalReliabilityPanel({ view }: Props) {
  const [state, setState] = useState<OperationalReliabilityState | null>(null);
  const [detail, setDetail] = useState<{ summary: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "reliability-continuous-verification") {
        setDetail(await fetchContinuousVerification());
      } else if (view === "reliability-recovery-orchestration") {
        setDetail(await fetchRecoveryOrchestration());
      } else if (view === "reliability-drift-intelligence") {
        setDetail(await fetchDriftIntelligence());
      } else if (view === "reliability-predictive-operations" || view === "reliability-operational-trajectory") {
        setDetail(await fetchPredictiveOperations());
      } else if (view === "reliability-production-confidence" || view === "reliability-confidence-forecasting") {
        const conf = await fetchProductionConfidence();
        setDetail({ summary: conf.narrative });
        setState((prev) => ({ ...(prev || { ok: true, phase: "11.3", summary: conf.narrative }), production_confidence: conf } as OperationalReliabilityState));
      } else {
        setState(await fetchOperationalReliabilityState());
      }
      if (view === "reliability-reliability-memory") {
        const full = await fetchOperationalReliabilityState();
        setState(full);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load operational reliability");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const title = titles[view] ?? "Operational Reliability";
  const harness = state?.harness;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Continuous operational verification and recovery orchestration — persistent production reliability assurance.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.harness_version ? (
        <div style={cardStyle}>
          <span style={{ fontSize: 11, color: mcColors.textDim }}>Reliability Harness {state.harness_version}</span>
          {state.production_reliable !== undefined ? (
            <p style={{ margin: "8px 0 0", color: state.production_reliable ? mcColors.green : mcColors.amber }}>
              Production reliable: {String(state.production_reliable)}
            </p>
          ) : null}
        </div>
      ) : null}

      {detail ? (
        <div style={cardStyle}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{detail.summary}</pre>
        </div>
      ) : null}

      {view === "reliability-production-confidence" && state?.production_confidence?.trust ? (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Trust score</span>
          <p style={{ margin: "8px 0 0", color: maturityColor(state.production_confidence.trust.qualification_tier) }}>
            {state.production_confidence.trust.qualification_tier} ·{" "}
            {Math.round((state.production_confidence.trust.infrastructure_trust_score ?? 0) * 100)}%
          </p>
        </div>
      ) : null}

      {state?.capabilities && view === "reliability-reliability-memory" && (
        <div style={{ marginTop: 8 }}>
          {Object.entries(state.capabilities).map(([key, val]) => (
            <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
              <span>{key.replace(/_/g, " ")}</span>
              <span style={{ color: maturityColor(val) }}>{val}</span>
            </div>
          ))}
        </div>
      )}

      {view === "reliability-continuous-verification" && !detail && state?.continuous_verification ? (
        <div style={cardStyle}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
            {state.continuous_verification.summary}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
