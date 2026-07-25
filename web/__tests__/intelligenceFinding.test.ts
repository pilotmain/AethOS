import { describe, expect, it } from "vitest";

import {
  anomalyToIntelligenceFinding,
  buildOverviewIntelligenceFindings,
  recommendationToIntelligenceFinding,
} from "@/lib/missionControl/intelligenceFinding";
import { buildOperationalNarrative } from "@/lib/missionControl/operationalStorytelling";

describe("intelligenceFinding", () => {
  it("builds replay degradation finding with evidence and recommended review", () => {
    const findings = buildOverviewIntelligenceFindings({
      priorityIssue: "replay continuity during long-running sessions",
      confidence: 0.61,
      confidenceLabel: "moderate",
      replayDegraded: true,
    });
    expect(findings[0]?.finding).toContain("Replay integrity degraded");
    expect(findings[0]?.evidence.length).toBeGreaterThan(0);
    expect(findings[0]?.recommendedReview.some((r) => r.includes("evidence bundle"))).toBe(true);
    expect(findings[0]?.confidence).toBe(0.61);
  });

  it("maps anomalies to structured findings", () => {
    const finding = anomalyToIntelligenceFinding({
      anomaly_id: "a1",
      kind: "replay_integrity",
      severity: "medium",
      confidence: 0.82,
      evidence: ["integrity score 0.84 → 0.61"],
      related_systems: ["replay"],
      recommended_action: "Compare replay continuity",
    });
    expect(finding.finding).toContain("replay integrity");
    expect(finding.evidence[0]).toContain("0.84");
    expect(finding.recommendedReview[0]).toContain("Compare replay continuity");
  });

  it("maps recommendations to structured findings", () => {
    const finding = recommendationToIntelligenceFinding({
      recommendation_id: "r1",
      title: "Validate replay stitching",
      severity: "low",
      confidence: 0.75,
      observed: ["telemetry freshness degraded"],
      suggested_action: "Run intelligence cycle",
      approval_required: true,
    });
    expect(finding.finding).toContain("Validate replay stitching");
    expect(finding.impact).toContain("blocked");
  });
});

describe("operationalStorytelling — hardened presentation", () => {
  it("returns structured findings and evidence-first dominant narrative", () => {
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity during long-running sessions",
      confidence: 0.61,
      confidenceLabel: "moderate",
      replayDegraded: true,
    });
    expect(narrative.structuredFindings.length).toBeGreaterThan(0);
    expect(narrative.dominantNarrative).toContain("Replay integrity degraded");
    expect(narrative.primaryStory).toContain("0.61");
  });

  it("retains optional companion recovery narrative without using it as dominant output", () => {
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity during long-running sessions",
      confidence: 0.86,
      confidenceLabel: "high",
      recentlyResolved: true,
    });
    expect(narrative.recoveryStory).toContain("calm operational rhythm");
    expect(narrative.dominantNarrative).not.toContain("calm operational rhythm");
  });
});
