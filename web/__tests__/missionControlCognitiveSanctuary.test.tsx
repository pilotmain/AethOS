import { describe, expect, it } from "vitest";

import { computeCognitiveSanctuary, assessCognitiveSanctuaryField } from "@/lib/missionControl/cognitiveSanctuary";
import { assessCognitiveSustainability } from "@/lib/missionControl/cognitiveSustainability";
import { assessEmotionalResilience } from "@/lib/missionControl/emotionalResilience";
import { assessFlowContinuity } from "@/lib/missionControl/flowContinuity";
import { computeOperationalConsciousness } from "@/lib/missionControl/operationalConsciousness";
import {
  buildOperationalNarrative,
  compressOperationalEventsV6,
} from "@/lib/missionControl/operationalStorytelling";
import { resolveSanctuaryAttention } from "@/lib/missionControl/spatialHierarchy";

describe("cognitiveSanctuary", () => {
  it("protects sustained cognition during prolonged investigation", () => {
    const sanctuary = computeCognitiveSanctuary(
      { replayIntegrityDegraded: true, hasActiveJobs: true, pendingRecommendations: 7 },
      { focusMode: true, priorityIssue: "replay continuity validation" },
    );
    expect(sanctuary.sanctuary.sustainedCognitiveProtection).toBe(true);
    expect(sanctuary.sanctuary.immersiveContinuity).toBe(true);
    expect(sanctuary.flowContinuity.investigationContinuityMemory).toBe(true);
    expect(sanctuary.sanctuaryImmersion).toBe(true);
  });

  it("enters restoring sanctuary after stabilization", () => {
    const ops = computeOperationalConsciousness({}, { recentlyResolved: true, confidence: 0.9 });
    const field = assessCognitiveSanctuaryField({}, ops, { recentlyResolved: true });
    expect(field.sanctuaryState).toBe("restoring");
  });
});

describe("flowContinuity", () => {
  it("shields interruptions and preserves narrative momentum", () => {
    const ops = computeOperationalConsciousness({ replayIntegrityDegraded: true, pendingRecommendations: 7 }, { focusMode: true });
    const continuity = assessFlowContinuity({ replayIntegrityDegraded: true }, ops, { focusMode: true });
    expect(continuity.interruptionShielding).toBe(true);
    expect(continuity.silentFocusProtection).toBe(true);
    expect(continuity.maxSurfaces).toBe(1);
    expect(continuity.suppressPeripheralSignals).toBe(true);
  });
});

describe("emotionalResilience", () => {
  it("communicates calm operational rhythm after recovery", () => {
    const ops = computeOperationalConsciousness({}, { recentlyResolved: true, confidence: 0.88 });
    const resilience = assessEmotionalResilience({}, ops, { recentlyResolved: true, confidence: 0.88 });
    expect(resilience.recoveryPacing).toBe(true);
    expect(resilience.recoveryNarrative).toContain("settling back into a calm operational rhythm");
  });
});

describe("cognitiveSustainability", () => {
  it("compresses recommendations into invisible partnership phrase", () => {
    const ops = computeOperationalConsciousness(
      { pendingRecommendations: 7, replayIntegrityDegraded: true },
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    const sustainability = assessCognitiveSustainability(
      { pendingRecommendations: 7, replayIntegrityDegraded: true },
      ops,
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    expect(sustainability.partnerHeadline).toContain("highest-impact unresolved area");
    expect(sustainability.confidenceRestraint).toBe(true);
  });
});

describe("sanctuaryAttention", () => {
  it("resolves invisible attention during sanctuary immersion", () => {
    expect(
      resolveSanctuaryAttention({
        mood: "elevated",
        sanctuaryState: "immersive",
        recovery: false,
        tension: 0.4,
        sanctuaryImmersion: true,
      }),
    ).toBe("invisible");
  });

  it("resolves atmospheric attention during grounded state", () => {
    expect(
      resolveSanctuaryAttention({
        mood: "informational",
        sanctuaryState: "grounded",
        recovery: false,
        tension: 0.2,
      }),
    ).toBe("atmospheric");
  });
});

describe("narrativeCompressionV6", () => {
  it("converges operational complexity with continued stability reassurance", () => {
    const compressed = compressOperationalEventsV6({
      replayAlertCount: 6,
      telemetryAlertCount: 3,
      recommendationCount: 4,
      recoveryNotices: 1,
      confidenceChanges: 2,
      confidenceWarnings: 1,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("persists across extended operational sessions");
    expect(compressed[0]).toContain("overall operational stability continues to remain steady");
  });

  it("integrates emotional resilience into narrative", () => {
    const sanctuary = computeCognitiveSanctuary({}, { recentlyResolved: true, confidence: 0.9 });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity",
      confidence: 0.9,
      confidenceLabel: "strong",
      recentlyResolved: true,
      emotionalResilience: sanctuary.emotionalResilience,
      cognitiveSustainability: sanctuary.cognitiveSustainability,
    });
    expect(narrative.recoveryStory).toContain("settling back into a calm operational rhythm");
  });
});

describe("operationalCognitiveSanctuary", () => {
  it("orchestrates full sanctuary stack", () => {
    const sanctuary = computeCognitiveSanctuary({});
    expect(sanctuary.ops.cognition).toBeDefined();
    expect(sanctuary.sanctuary).toBeDefined();
    expect(sanctuary.flowContinuity).toBeDefined();
    expect(sanctuary.emotionalResilience).toBeDefined();
    expect(sanctuary.cognitiveSustainability).toBeDefined();
    expect(sanctuary.sanctuaryClassName).toContain("mc-sanctuary-");
  });
});
