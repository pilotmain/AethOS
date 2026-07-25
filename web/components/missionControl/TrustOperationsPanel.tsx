"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchReliabilityConfidence,
  fetchReliabilityCorrelation,
  fetchReliabilityGovernance,
  fetchReliabilityReplay,
  fetchReliabilityScores,
  fetchReliabilityState,
  reconstructReliabilityReplay,
  retryReliabilityRecovery,
  type ReliabilityState,
} from "@/lib/missionControl/reliabilityApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const trustColor = (level?: string) => {
  if (level === "high" || level === "verified_healthy") return mcColors.cyan;
  if (level === "degraded" || level === "degraded_confidence") return mcColors.amber;
  if (level === "low" || level === "verification_failed") return mcColors.red;
  return mcColors.textMuted;
};

const titles: Record<string, string> = {
  "trust-authority": "Reliability Authority",
  "trust-replay": "Replay Intelligence",
  "trust-governance": "Governance Drift",
  "trust-confidence": "Confidence Center",
  "trust-signal-quality": "Signal Quality",
  "trust-correlation": "Correlation Graph",
  "trust-metrics": "Trust Metrics",
  "trust-recovery": "Recovery Runtime",
};

export function TrustOperationsPanel({ view }: Props) {
  const [state, setState] = useState<ReliabilityState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "trust-metrics") {
        const scores = await fetchReliabilityScores();
        setState({ ok: true, scores: scores.scores, reliability: scores.reliability as ReliabilityState["reliability"] });
      } else if (view === "trust-confidence") {
        const conf = await fetchReliabilityConfidence();
        setState({
          ok: true,
          reliability: { truth_state: conf.truth_state, bounded_confidence: (conf.confidence as { bounded_confidence?: number })?.bounded_confidence },
          explainability: { confidence: conf.explainability },
        });
      } else if (view === "trust-governance") {
        const gov = await fetchReliabilityGovernance();
        setState({ ok: true, governance: gov.governance, explainability: { governance: gov.explainability } });
      } else if (view === "trust-replay") {
        const replay = await fetchReliabilityReplay();
        setState({ ok: true, reconstruction: replay as ReliabilityState["reconstruction"] });
      } else if (view === "trust-correlation") {
        const corr = await fetchReliabilityCorrelation();
        setState({ ok: true, correlation: corr.correlation });
      } else {
        setState(await fetchReliabilityState());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reliability state");
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const onReconstruct = async () => {
    setBusy(true);
    try {
      await reconstructReliabilityReplay();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const onRecovery = async (action: string) => {
    setBusy(true);
    try {
      await retryReliabilityRecovery(action);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const rel = state?.reliability;
  const scores = state?.scores;
  const gov = state?.governance;
  const fatigue = state?.fatigue;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Operational Trust"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Reliability-centric operations — bounded confidence, explainable governance, never self-authorizing.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {view === "trust-replay" ? (
            <button type="button" disabled={busy} onClick={onReconstruct} style={mcButtonSecondaryStyle}>
              Reconstruct
            </button>
          ) : null}
          <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {(view === "trust-authority" || view === "trust-metrics") && rel ? (
        <div style={{ marginTop: 16 }}>
          <div style={{ ...cardStyle, borderLeft: `3px solid ${trustColor(rel.truth_state)}` }}>
            <div style={{ fontWeight: 600 }}>Truth state: {rel.truth_state}</div>
            <div style={{ color: mcColors.textDim, marginTop: 4 }}>
              Executed: {String(rel.executed)} · Verified: {String(rel.verified)} · Confidence: {rel.bounded_confidence ?? "—"} (bounded)
            </div>
            <div style={{ color: mcColors.textMuted, marginTop: 4, fontSize: 12 }}>{rel.summary}</div>
          </div>
          {scores ? (
            <div style={cardStyle}>
              <div style={{ fontWeight: 600 }}>Global reliability: {scores.global_reliability_score} ({scores.trust_level})</div>
              <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 6 }}>
                {Object.entries(scores.dimensions ?? {})
                  .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
                  .join(" · ")}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {view === "trust-governance" && gov ? (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Tier: {String(gov.current_tier)} {gov.escalated ? "(escalated)" : ""}</div>
            {gov.cooldown_active ? <div style={{ color: mcColors.amber, marginTop: 4 }}>Cooldown active — restart mutations restricted</div> : null}
            <div style={{ color: mcColors.textMuted, marginTop: 6, fontSize: 12 }}>{String(gov.escalation_reason || "")}</div>
          </div>
          {state?.explainability?.governance ? (
            <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{String(state.explainability.governance)}</pre>
          ) : null}
        </div>
      ) : null}

      {view === "trust-confidence" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600, color: trustColor(rel?.truth_state) }}>{rel?.truth_state ?? "—"}</div>
            <div style={{ marginTop: 4 }}>Bounded confidence: {rel?.bounded_confidence ?? "—"}</div>
          </div>
          {state?.explainability?.confidence ? (
            <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{String(state.explainability.confidence)}</pre>
          ) : null}
        </div>
      )}

      {view === "trust-signal-quality" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Fatigue score: {fatigue?.fatigue_score ?? "—"}</div>
            <div style={{ color: mcColors.textDim, marginTop: 4 }}>{fatigue?.summary ?? "Signal quality metrics from presence fatigue prevention."}</div>
            <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>
              Surfaced: {fatigue?.surfaced_count ?? "—"} · Noise ratio: {scores?.dimensions?.signal_noise_ratio ?? "—"}
            </div>
          </div>
        </div>
      )}

      {view === "trust-correlation" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>Correlation strength: {state?.correlation?.correlation_strength ?? "—"}</div>
          {(state?.correlation?.correlations ?? []).map((c, i) => (
            <div key={i} style={cardStyle}>
              <div style={{ fontWeight: 600 }}>{c.pattern}</div>
              <div style={{ color: mcColors.textMuted, marginTop: 4 }}>{c.summary}</div>
              <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>{c.domains?.join(" → ")}</div>
            </div>
          ))}
        </div>
      )}

      {view === "trust-replay" && (
        <div style={{ marginTop: 16 }}>
          {state?.reconstruction?.operational_story ? (
            <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12 }}>{state.reconstruction.operational_story}</pre>
          ) : (
            <p style={{ color: mcColors.textMuted }}>No replay reconstruction yet.</p>
          )}
          {(state?.reconstruction?.causal_chains ?? []).map((chain, i) => (
            <div key={i} style={cardStyle}>
              <div style={{ fontWeight: 600 }}>Chain {i + 1} (conf {chain.confidence})</div>
              <div style={{ marginTop: 4 }}>{chain.steps?.join(" → ")}</div>
            </div>
          ))}
        </div>
      )}

      {view === "trust-recovery" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            Degraded mode: {state?.recovery?.degraded_mode ? "active" : "inactive"}
          </div>
          {(state?.recovery?.recovery_options ?? []).map((opt) => (
            <div key={opt.action} style={{ ...cardStyle, display: "flex", justifyContent: "space-between", gap: 8 }}>
              <span>{opt.label}</span>
              <button type="button" disabled={busy} onClick={() => onRecovery(opt.action ?? "")} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
                Retry (bounded)
              </button>
            </div>
          ))}
          {!state?.recovery?.recovery_options?.length ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No recovery actions recommended — system within normal bounds.</p>
          ) : null}
        </div>
      )}
    </section>
  );
}
