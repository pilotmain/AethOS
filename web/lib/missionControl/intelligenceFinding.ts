/** Mission Control intelligence finding — evidence-first operational structure. */

import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import type {
  OperationalAnomaly,
  OperationalIntelligenceState,
  OperationalRecommendation,
} from "@/lib/missionControl/intelligenceApi";

export type IntelligenceFinding = {
  id: string;
  finding: string;
  evidence: string[];
  confidence: number | null;
  confidenceReason: string;
  impact: string;
  recommendedReview: string[];
  /** Optional companion commentary — never replaces evidence sections. */
  companionCommentary?: string | null;
  severity?: "low" | "medium" | "high" | "informational";
};

export type StructuredFindingInput = {
  priorityIssue: string;
  confidence: number;
  confidenceLabel: string;
  replayDegraded?: boolean;
  anomalyCount?: number;
  preflightActive?: boolean;
  recentlyResolved?: boolean;
  pendingRecommendations?: number;
  replayDetail?: string;
  reasoning?: string;
};

const sectionLabel = {
  finding: "Finding",
  evidence: "Evidence",
  confidence: "Confidence",
  impact: "Impact",
  recommendedReview: "Recommended review",
  companionCommentary: "Companion commentary",
} as const;

export { sectionLabel };

export function formatConfidence(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

export function buildOverviewIntelligenceFindings(input: StructuredFindingInput): IntelligenceFinding[] {
  const findings: IntelligenceFinding[] = [];
  const issue = input.priorityIssue.replace(/^the /i, "");

  if (input.replayDegraded) {
    findings.push({
      id: "replay-integrity-degraded",
      finding: "Replay integrity degraded during long-running sessions.",
      evidence: [
        "Replay continuity signals observed across extended operational sessions.",
        input.replayDetail
          ? `Replay detail: ${firstLine(input.replayDetail)}`
          : "Temporal anchor continuity may be partially missing.",
        `Operational confidence: ${formatConfidence(input.confidence)} (${input.confidenceLabel}).`,
      ].filter(Boolean),
      confidence: input.confidence,
      confidenceReason:
        input.reasoning?.trim() ||
        "Route integrity may remain verified while replay stitching confidence is reduced when telemetry freshness is degraded.",
      impact:
        "Long-session replay narratives may be less reliable. No evidence in current signals indicates production instability.",
      recommendedReview: [
        "Compare replay continuity before and after scheduler cycles.",
        "Review memory compression effects on temporal anchors.",
        "Validate replay stitching against evidence bundle exports.",
      ],
      severity: input.confidence < 0.65 ? "medium" : "low",
    });
  }

  if ((input.pendingRecommendations ?? 0) > 0) {
    findings.push({
      id: "pending-recommendations",
      finding: `${input.pendingRecommendations} operational recommendation(s) pending operator review.`,
      evidence: [
        `${input.pendingRecommendations} recommendation(s) queued in operational intelligence.`,
        `Current focus area: ${issue}.`,
      ],
      confidence: input.confidence,
      confidenceReason: "Recommendation confidence derives from anomaly evidence and operational observations.",
      impact: "Governed changes may remain blocked until recommendations are reviewed or dismissed.",
      recommendedReview: [
        "Open the recommendation queue and validate highest-severity items first.",
        "Generate preflights where approval is required before execution.",
      ],
      severity: (input.pendingRecommendations ?? 0) > 2 ? "medium" : "low",
    });
  }

  if ((input.anomalyCount ?? 0) > 0 && !input.replayDegraded) {
    findings.push({
      id: "operational-anomalies",
      finding: `${input.anomalyCount} active operational anomal${input.anomalyCount === 1 ? "y" : "ies"} detected.`,
      evidence: [
        `${input.anomalyCount} anomaly signal(s) in the current observation window.`,
        `Telemetry / operational memory scan confidence: ${formatConfidence(input.confidence)}.`,
      ],
      confidence: input.confidence,
      confidenceReason: "Anomaly confidence reflects evidence density from the latest reality loop cycle.",
      impact: "Operational observations warrant review; severity depends on anomaly kind and related systems.",
      recommendedReview: [
        "Review active anomalies in Operational Intelligence.",
        "Run an intelligence cycle if observations are stale.",
      ],
      severity: (input.anomalyCount ?? 0) > 2 ? "medium" : "low",
    });
  }

  if (input.preflightActive) {
    findings.push({
      id: "active-preflights",
      finding: "Engineering preflights are active and awaiting operator review.",
      evidence: ["Preflight gates are open in the software delivery lane."],
      confidence: input.confidence,
      confidenceReason: "Preflight state is observable from governed delivery workflow signals.",
      impact: "Execution remains blocked until preflight review completes.",
      recommendedReview: ["Review active preflights before approving governed mutations."],
      severity: "informational",
    });
  }

  if (findings.length === 0) {
    findings.push({
      id: "operational-steady",
      finding:
        input.recentlyResolved || input.confidence >= 0.82
          ? "Operational signals are stable with no active anomalies or pending recommendations."
          : `Operational focus remains ${issue}.`,
      evidence: [
        `Confidence: ${formatConfidence(input.confidence)} (${input.confidenceLabel}).`,
        input.recentlyResolved
          ? "Recent recovery signals observed in companion quality metrics."
          : "No replay degradation or anomaly escalation in current navigation context.",
      ],
      confidence: input.confidence,
      confidenceReason:
        input.reasoning?.trim() ||
        "Confidence reflects partner brief synthesis and companion quality metrics.",
      impact:
        input.recentlyResolved
          ? "No immediate operator action required; continue periodic replay validation on long sessions."
          : "Monitor replay integrity on extended sessions before broader rollout.",
      recommendedReview: [
        "Refresh operational intelligence if observations age beyond telemetry freshness thresholds.",
        "Expand replay reasoning if confidence drops below review threshold.",
      ],
      severity: "informational",
    });
  }

  return findings;
}

export function anomalyToIntelligenceFinding(anomaly: OperationalAnomaly): IntelligenceFinding {
  const kind = (anomaly.kind ?? "unknown").replace(/_/g, " ");
  return {
    id: anomaly.anomaly_id ?? `anomaly-${kind}`,
    finding: `${kind} detected (${anomaly.severity ?? "unknown"} severity).`,
    evidence: [
      ...(anomaly.evidence ?? []),
      anomaly.related_systems?.length
        ? `Related systems: ${anomaly.related_systems.join(", ")}`
        : "Related systems: not specified",
    ],
    confidence: anomaly.confidence ?? null,
    confidenceReason: "Confidence scored from operational observation evidence in the anomaly engine.",
    impact: `Operational ${kind} may affect governed delivery or observability until validated.`,
    recommendedReview: [
      anomaly.recommended_action ?? "Review anomaly evidence and related systems.",
      "Correlate with telemetry freshness and replay exports if replay-related.",
    ].filter(Boolean),
    severity: normalizeSeverity(anomaly.severity),
  };
}

export function recommendationToIntelligenceFinding(rec: OperationalRecommendation): IntelligenceFinding {
  return {
    id: rec.recommendation_id ?? `rec-${rec.title ?? "unknown"}`,
    finding: rec.title ?? "Operational recommendation pending review.",
    evidence: [
      ...(rec.observed ?? []),
      rec.approval_required ? "Approval required before governed execution." : "Approval not required.",
      rec.autonomous_execution_blocked !== false ? "Autonomous execution blocked." : "",
    ].filter(Boolean),
    confidence: rec.confidence ?? null,
    confidenceReason: "Recommendation confidence derived from linked anomaly evidence.",
    impact: rec.approval_required
      ? "Governed mutation blocked until operator approval or preflight completion."
      : "Advisory recommendation — validate before acting.",
    recommendedReview: [
      rec.suggested_action ?? "Review suggested action and dismiss or snooze if not applicable.",
      rec.preflight_id ? `Existing preflight: ${rec.preflight_id}` : "Generate preflight if approval is required.",
    ].filter(Boolean),
    severity: normalizeSeverity(rec.severity),
  };
}

export function driftToIntelligenceFinding(
  drift: NonNullable<OperationalIntelligenceState["drift"]>,
): IntelligenceFinding | null {
  if (!drift.detected) return null;
  return {
    id: "operational-drift",
    finding: "Operational drift detected across observation signals.",
    evidence: drift.signals ?? ["Drift detection flagged by reality loop."],
    confidence: drift.confidence ?? null,
    confidenceReason: "Drift confidence reflects correlated signal divergence in operational memory.",
    impact: "Configuration or behavior may diverge from expected baseline — validate before promotion.",
    recommendedReview: [
      "Review drift signals and compare against last known stable cycle.",
      "Export evidence bundle for audit if drift persists.",
    ],
    severity: normalizeSeverity(drift.severity),
  };
}

export function telemetryFreshnessToIntelligenceFinding(
  freshness: NonNullable<OperationalIntelligenceState["telemetry_freshness"]>,
): IntelligenceFinding | null {
  if (!freshness.stale) return null;
  return {
    id: "telemetry-freshness-degraded",
    finding: "Telemetry freshness degraded — observations may be stale.",
    evidence: [
      ...(freshness.stale_sources ?? []).map((s) => `Stale source: ${s}`),
      freshness.age_hours != null ? `Last event age: ${freshness.age_hours.toFixed(1)}h` : "",
    ].filter(Boolean),
    confidence: null,
    confidenceReason: "Freshness is objective — based on last observed event timestamps.",
    impact: "Intelligence findings and replay stitching may be less reliable until telemetry refreshes.",
    recommendedReview: [
      "Run an operational intelligence cycle.",
      "Verify scheduler and reality loop are producing fresh observations.",
    ],
    severity: "medium",
  };
}

export function buildContextFindingSummary(context: NavigationContext, confidence: number): IntelligenceFinding[] {
  const findings: IntelligenceFinding[] = [];
  if (context.replayIntegrityDegraded) {
    findings.push({
      id: "nav-replay-degraded",
      finding: "Replay integrity degraded (navigation context).",
      evidence: ["Navigation context flags replay integrity degradation."],
      confidence,
      confidenceReason: "Context signal from Mission Control shell observability.",
      impact: "Replay-dependent workflows should be validated before relying on long-session narratives.",
      recommendedReview: ["Open intelligence replay view and compare continuity markers."],
      severity: "medium",
    });
  }
  return findings;
}

function normalizeSeverity(sev?: string): IntelligenceFinding["severity"] {
  if (sev === "high") return "high";
  if (sev === "medium") return "medium";
  if (sev === "low") return "low";
  return "informational";
}

function firstLine(text: string): string {
  return text.split("\n")[0]?.trim() ?? text;
}
