import { describe, expect, it } from "vitest";

import {
  assessCognitiveFlow,
  computeInvisibleOperationalIntelligence,
} from "@/lib/missionControl/cognitiveFlow";
import { computeCognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import { assessEmotionalStability } from "@/lib/missionControl/emotionalStability";
import { assessInvisibleAssistance } from "@/lib/missionControl/invisibleAssistance";
import {
  buildOperationalNarrative,
  compressOperationalEventsV4,
} from "@/lib/missionControl/operationalStorytelling";
import { resolveCalmAttention } from "@/lib/missionControl/spatialHierarchy";
import { assessTrustAtmosphere } from "@/lib/missionControl/trustAtmosphere";

describe("cognitiveFlow", () => {
  it("protects flow during deep focus immersion", () => {
    const intelligence = computeInvisibleOperationalIntelligence(
      { replayIntegrityDegraded: true, hasActiveJobs: true },
      { focusMode: true },
    );
    expect(intelligence.flow.flowState).toBe("immersed");
    expect(intelligence.flow.minimizeMotion).toBe(true);
    expect(intelligence.flow.suppressSecondaryDomains).toBe(true);
    expect(intelligence.immersionActive).toBe(true);
  });

  it("sustains investigating flow under replay pressure", () => {
    const intelligence = computeInvisibleOperationalIntelligence({ replayIntegrityDegraded: true });
    expect(intelligence.flow.flowState).toBe("investigating");
    expect(intelligence.flow.enlargeInvestigationNarrative).toBe(true);
    expect(intelligence.flow.pauseWeakRecommendations).toBe(true);
  });

  it("enters recovering flow after resolution", () => {
    const presence = computeCognitiveOperationalPresence({}, { recentlyResolved: true, confidence: 0.88 });
    const flow = assessCognitiveFlow({}, presence, { recentlyResolved: true });
    expect(flow.flowState).toBe("recovering");
    expect(flow.reduceEnvironmentalVariation).toBe(true);
  });
});

describe("invisibleAssistance", () => {
  it("provides passive guidance without attention-seeking during immersion", () => {
    const intelligence = computeInvisibleOperationalIntelligence(
      { replayIntegrityDegraded: true },
      { focusMode: true },
    );
    expect(intelligence.assistance.suppressAttentionSeeking).toBe(true);
    expect(intelligence.assistance.maxVisibleSurfaces).toBe(1);
    expect(intelligence.assistance.passiveGuidance).toContain("invisibly");
  });

  it("restrains recommendations under flow protection", () => {
    const presence = computeCognitiveOperationalPresence({ replayIntegrityDegraded: true, hasActiveJobs: true });
    const flow = assessCognitiveFlow({ replayIntegrityDegraded: true, hasActiveJobs: true }, presence);
    const assistance = assessInvisibleAssistance({ replayIntegrityDegraded: true, hasActiveJobs: true }, presence, flow);
    expect(assistance.recommendationRestraint).toBe(true);
    expect(assistance.silentSimplification).toBe(true);
  });
});

describe("trustAtmosphere", () => {
  it("uses calibrated atmosphere phrase instead of system healthy", () => {
    const presence = computeCognitiveOperationalPresence({ replayIntegrityDegraded: true }, { confidence: 0.8 });
    const trust = assessTrustAtmosphere({ replayIntegrityDegraded: true }, presence, {
      confidence: 0.8,
      replayDegraded: true,
    });
    expect(trust.atmospherePhrase).toContain("Operational stability remains strong");
    expect(trust.atmospherePhrase).toContain("replay continuity");
    expect(trust.visualHonesty).toBe(true);
  });

  it("signals recovery calmness after stabilization", () => {
    const presence = computeCognitiveOperationalPresence({}, { recentlyResolved: true, confidence: 0.88 });
    const trust = assessTrustAtmosphere({}, presence, { recentlyResolved: true, confidence: 0.88 });
    expect(trust.recoveryCalmness).toBe(true);
    expect(trust.atmospherePhrase).toContain("reliability convergence");
  });
});

describe("emotionalStability", () => {
  it("reduces tension during immersive flow", () => {
    const intelligence = computeInvisibleOperationalIntelligence(
      { hasAnomalies: true, replayIntegrityDegraded: true },
      { focusMode: true },
    );
    expect(intelligence.emotionalStability.tensionBalance).toBeLessThan(0.5);
    expect(intelligence.emotionalStability.fatigueAwarePacing).toBeDefined();
  });

  it("decompresses emotionally after recovery", () => {
    const presence = computeCognitiveOperationalPresence({}, { recentlyResolved: true, confidence: 0.9 });
    const flow = assessCognitiveFlow({}, presence, { recentlyResolved: true });
    const stability = assessEmotionalStability({}, presence, flow, { recentlyResolved: true, confidence: 0.9 });
    expect(stability.recoveryDecompression).toBe(true);
    expect(stability.cognitiveReassurance).toContain("decompression");
  });
});

describe("calmAttentionArchitecture", () => {
  it("resolves invisible attention during recovery", () => {
    expect(resolveCalmAttention({ mood: "stable", flowState: "recovering", recovery: true, tension: 0.1 })).toBe(
      "invisible",
    );
  });

  it("resolves invisible attention during immersion", () => {
    expect(resolveCalmAttention({ mood: "elevated", flowState: "immersive", recovery: false, tension: 0.4 })).toBe(
      "invisible",
    );
  });
});

describe("narrativeCompressionV4", () => {
  it("converges repeated events into one calm narrative", () => {
    const compressed = compressOperationalEventsV4({
      replayAlertCount: 5,
      telemetryAlertCount: 3,
      recommendationCount: 4,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("continues across extended operational sessions");
    expect(compressed[0]).toContain("operational stability remains steady");
  });

  it("integrates companion realism in narrative", () => {
    const intelligence = computeInvisibleOperationalIntelligence({ replayIntegrityDegraded: true, pendingRecommendations: 3 });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity during extended operational sessions",
      confidence: 0.76,
      confidenceLabel: "moderate",
      replayDegraded: true,
      pendingRecommendations: 3,
      dominantThought: intelligence.assistance.passiveGuidance,
      compression: { replayAlertCount: 5, telemetryAlertCount: 3, recommendationCount: 3 },
    });
    expect(narrative.companionHeadline).toContain("highest-impact unresolved area");
    expect(narrative.compressedAlerts[0]).toContain("persists across extended operational sessions");
  });
});

describe("invisibleOperationalIntelligence", () => {
  it("orchestrates full invisible intelligence stack", () => {
    const intelligence = computeInvisibleOperationalIntelligence({});
    expect(intelligence.presence).toBeDefined();
    expect(intelligence.flow).toBeDefined();
    expect(intelligence.assistance).toBeDefined();
    expect(intelligence.trustAtmosphere).toBeDefined();
    expect(intelligence.emotionalStability).toBeDefined();
    expect(intelligence.intelligenceClassName).toContain("mc-flow-sustained");
  });
});
