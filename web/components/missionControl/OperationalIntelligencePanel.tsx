"use client";

import { useCallback, useEffect, useState } from "react";

import { IntelligenceFindingCard } from "@/components/missionControl/IntelligenceFindingCard";
import {
  anomalyToIntelligenceFinding,
  driftToIntelligenceFinding,
  recommendationToIntelligenceFinding,
  telemetryFreshnessToIntelligenceFinding,
} from "@/lib/missionControl/intelligenceFinding";
import {
  dismissRecommendation,
  fetchOperationalIntelligenceState,
  generatePreflightFromRecommendation,
  runOperationalCycle,
  snoozeRecommendation,
  type OperationalAnomaly,
  type OperationalIntelligenceState,
  type OperationalRecommendation,
} from "@/lib/missionControl/intelligenceApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  view: MissionControlView;
};

const titles: Record<string, string> = {
  "operational-anomalies": "Active Anomalies",
  "operational-drift": "Drift Detection",
  "deployment-stability": "Deployment Stability",
  "cross-provider-correlation": "Cross-Provider Correlation",
  "workflow-health": "Workflow Health",
  "dependency-risk": "Dependency Risk",
  "recommendation-queue": "Recommendation Queue",
  "telemetry-freshness": "Telemetry Freshness",
  "intelligence-replay": "Operational Replay",
};

export function OperationalIntelligencePanel({ view }: Props) {
  const [state, setState] = useState<OperationalIntelligenceState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchOperationalIntelligenceState();
      setState(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load operational intelligence");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onCycle = async () => {
    setBusyId("cycle");
    try {
      await runOperationalCycle();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cycle failed");
    } finally {
      setBusyId(null);
    }
  };

  const onDismiss = async (id: string) => {
    setBusyId(id);
    try {
      await dismissRecommendation(id);
      await load();
    } finally {
      setBusyId(null);
    }
  };

  const onSnooze = async (id: string) => {
    setBusyId(id);
    try {
      await snoozeRecommendation(id);
      await load();
    } finally {
      setBusyId(null);
    }
  };

  const onPreflight = async (id: string) => {
    setBusyId(id);
    try {
      await generatePreflightFromRecommendation(id);
      await load();
    } finally {
      setBusyId(null);
    }
  };

  const anomalies = state?.anomalies ?? [];
  const recommendations = state?.recommendations ?? [];
  const drift = state?.drift;
  const stability = state?.stability;
  const freshness = state?.telemetry_freshness;
  const replays = state?.replays ?? [];

  const renderAnomaly = (a: OperationalAnomaly) => (
    <IntelligenceFindingCard key={a.anomaly_id} finding={anomalyToIntelligenceFinding(a)} compact />
  );

  const renderRecommendation = (r: OperationalRecommendation) => (
    <div key={r.recommendation_id}>
      <IntelligenceFindingCard finding={recommendationToIntelligenceFinding(r)} compact />
      <div style={{ display: "flex", gap: 8, marginTop: -4, marginBottom: 12, flexWrap: "wrap" }}>
        {r.approval_required ? (
          <button type="button" disabled={busyId === r.recommendation_id} onClick={() => onPreflight(r.recommendation_id!)} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
            Generate preflight
          </button>
        ) : null}
        <button type="button" disabled={busyId === r.recommendation_id} onClick={() => onSnooze(r.recommendation_id!)} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
          Snooze
        </button>
        <button type="button" disabled={busyId === r.recommendation_id} onClick={() => onDismiss(r.recommendation_id!)} style={{ ...mcButtonSecondaryStyle, fontSize: 11, color: mcColors.amber }}>
          Ignore
        </button>
      </div>
    </div>
  );

  const driftFinding = drift ? driftToIntelligenceFinding(drift) : null;
  const freshnessFinding = freshness ? telemetryFreshnessToIntelligenceFinding(freshness) : null;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Operational Intelligence"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Evidence-first operational intelligence — finding, evidence, confidence, impact, and recommended review.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" onClick={onCycle} disabled={busyId === "cycle"} style={mcButtonSecondaryStyle}>
            Run cycle
          </button>
          <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {view === "operational-anomalies" && (
        <div style={{ marginTop: 16 }}>
          {anomalies.length === 0 ? (
            <p style={{ color: mcColors.textMuted }}>No active anomalies. Run a cycle or wait for scheduler observations.</p>
          ) : (
            anomalies.map(renderAnomaly)
          )}
        </div>
      )}

      {view === "operational-drift" && (
        <div style={{ marginTop: 16 }}>
          {driftFinding ? (
            <IntelligenceFindingCard finding={driftFinding} />
          ) : (
            <IntelligenceFindingCard
              finding={{
                id: "no-drift",
                finding: "No operational drift detected in the current observation window.",
                evidence: ["Drift detection returned no correlated signal divergence."],
                confidence: drift?.confidence ?? null,
                confidenceReason: "Absence of drift is an objective scan result from the reality loop.",
                impact: "No configuration divergence action required.",
                recommendedReview: ["Continue periodic intelligence cycles."],
                severity: "informational",
              }}
            />
          )}
        </div>
      )}

      {view === "deployment-stability" && (
        <div style={{ marginTop: 16 }}>
          <IntelligenceFindingCard
            finding={{
              id: "deployment-stability",
              finding: `Deployment stability: ${stability?.stability ?? "unknown"}.`,
              evidence: [
                `Event count: ${stability?.event_count ?? 0}`,
                ...(stability?.timeline ?? []).slice(0, 4).map(
                  (t) => `${t.at ? new Date(t.at * 1000).toLocaleString() : "—"} — ${t.detail ?? "event"}`,
                ),
              ],
              confidence: null,
              confidenceReason: "Stability assessment derived from deployment event timeline.",
              impact: "Elevated instability may warrant hold on promotion until replay and verification pass.",
              recommendedReview: ["Review deployment timeline entries for recurring failure patterns."],
              severity: stability?.stability === "unstable" ? "medium" : "informational",
            }}
          />
        </div>
      )}

      {view === "workflow-health" && (
        <div style={{ marginTop: 16 }}>
          {(state?.trends ?? []).filter((t) => t.toLowerCase().includes("workflow")).length > 0 ? (
            <IntelligenceFindingCard
              finding={{
                id: "workflow-trends",
                finding: "Workflow health trends observed.",
                evidence: (state?.trends ?? []).filter((t) => t.toLowerCase().includes("workflow")),
                confidence: null,
                confidenceReason: "Trend lines from operational memory scans.",
                impact: "Workflow instability may increase delivery friction until validated.",
                recommendedReview: ["Correlate workflow trends with active anomalies."],
                severity: "low",
              }}
            />
          ) : null}
          {anomalies.filter((a) => (a.kind ?? "").includes("workflow")).map(renderAnomaly)}
          {!anomalies.some((a) => (a.kind ?? "").includes("workflow")) && !(state?.trends ?? []).some((t) => t.includes("workflow")) ? (
            <p style={{ color: mcColors.textMuted }}>No workflow instability signals in current window.</p>
          ) : null}
        </div>
      )}

      {view === "dependency-risk" && (
        <div style={{ marginTop: 16 }}>
          {anomalies.filter((a) => (a.kind ?? "").includes("dependency")).map(renderAnomaly)}
          {(state?.recurring_patterns ?? []).filter((p) => p.includes("dependency")).length > 0 ? (
            <IntelligenceFindingCard
              finding={{
                id: "dependency-patterns",
                finding: "Recurring dependency risk patterns detected.",
                evidence: (state?.recurring_patterns ?? []).filter((p) => p.includes("dependency")),
                confidence: null,
                confidenceReason: "Pattern recurrence from operational memory.",
                impact: "Dependency drift may affect supply-chain or runtime assumptions.",
                recommendedReview: ["Review dependency anomalies and update lockfile governance if needed."],
                severity: "low",
              }}
            />
          ) : null}
        </div>
      )}

      {view === "recommendation-queue" && (
        <div style={{ marginTop: 16 }}>
          {recommendations.length === 0 ? (
            <p style={{ color: mcColors.textMuted }}>No active recommendations.</p>
          ) : (
            recommendations.map(renderRecommendation)
          )}
        </div>
      )}

      {view === "telemetry-freshness" && (
        <div style={{ marginTop: 16 }}>
          {freshnessFinding ? (
            <IntelligenceFindingCard finding={freshnessFinding} />
          ) : (
            <IntelligenceFindingCard
              finding={{
                id: "telemetry-fresh",
                finding: "Telemetry is fresh within acceptable observation windows.",
                evidence: [
                  freshness?.age_hours != null ? `Last event age: ${freshness.age_hours.toFixed(1)}h` : "No stale sources reported.",
                ],
                confidence: null,
                confidenceReason: "Freshness based on last observed event timestamps.",
                impact: "Intelligence findings should reflect current operational state.",
                recommendedReview: ["Continue scheduled intelligence cycles."],
                severity: "informational",
              }}
            />
          )}
        </div>
      )}

      {view === "intelligence-replay" && (
        <div style={{ marginTop: 16 }}>
          {replays.length === 0 ? (
            <p style={{ color: mcColors.textMuted }}>Replays appear after reality loop cycles.</p>
          ) : (
            replays.map((r) => (
              <IntelligenceFindingCard
                key={r.replay_id}
                compact
                finding={{
                  id: r.replay_id ?? "replay",
                  finding: `Operational replay ${r.replay_id} available for review.`,
                  evidence: [
                    `Anomaly count in replay: ${r.anomaly_count ?? 0}`,
                    r.created_at ? `Created: ${new Date(r.created_at * 1000).toLocaleString()}` : "",
                  ].filter(Boolean),
                  confidence: null,
                  confidenceReason: "Replay integrity scoring available in deep replay companion view.",
                  impact: "Replay exports support audit and continuity validation.",
                  recommendedReview: ["Open replay detail and compare against evidence bundle exports."],
                  severity: "informational",
                }}
              />
            ))
          )}
          <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 8 }}>
            Scheduler cycles: {state?.scheduler?.stats?.cycles ?? 0}
          </div>
        </div>
      )}
    </section>
  );
}
