import { describe, expect, it } from "vitest";

import {
  assessAmbientCognitiveFlow,
  computeAmbientCalmCognition,
} from "@/lib/missionControl/ambientCognitiveFlow";
import { assessCalmComputing } from "@/lib/missionControl/calmComputing";
import { computeCognitivePartnership } from "@/lib/missionControl/cognitivePartnership";
import { assessInvisibleGuidance } from "@/lib/missionControl/invisibleGuidance";
import { assessOperationalErgonomics } from "@/lib/missionControl/operationalErgonomics";
import {
  buildOperationalNarrative,
  compressOperationalEventsV4,
} from "@/lib/missionControl/operationalStorytelling";
import { resolveProtectedAttention } from "@/lib/missionControl/spatialHierarchy";

describe("ambientCognitiveFlow", () => {
  it("protects sustained cognition during extended investigation", () => {
    const cognition = computeAmbientCalmCognition(
      { replayIntegrityDegraded: true, hasActiveJobs: true, pendingRecommendations: 5 },
      { focusMode: true, priorityIssue: "replay continuity validation" },
    );
    expect(cognition.ambientFlow.thoughtContinuity).toBe(true);
    expect(cognition.ambientFlow.interruptionSuppressed).toBe(true);
    expect(cognition.ambientFlow.deepFocusEnvironment).toBe(true);
    expect(cognition.ambientFlow.ambientRhythmInvisible).toBe(true);
  });

  it("preserves investigating flow under replay pressure", () => {
    const cognition = computeAmbientCalmCognition({ replayIntegrityDegraded: true });
    expect(cognition.ambientFlow.flowState).toBe("investigating");
    expect(cognition.ambientFlow.investigationImmersion).toBe(true);
  });

  it("enters recovering ambient flow after stabilization", () => {
    const partnership = computeCognitivePartnership({}, { recentlyResolved: true, confidence: 0.9 });
    const flow = assessAmbientCognitiveFlow({}, partnership, { recentlyResolved: true });
    expect(flow.flowState).toBe("recovering");
    expect(flow.cognitiveRecoveryPacing).toBe(true);
  });
});

describe("invisibleGuidance", () => {
  it("minimizes recommendations without attention-seeking", () => {
    const cognition = computeAmbientCalmCognition({ replayIntegrityDegraded: true, pendingRecommendations: 5 }, { focusMode: true });
    expect(cognition.guidance.recommendationMinimized).toBe(true);
    expect(cognition.guidance.intelligentSilence).toBe(true);
    expect(cognition.guidance.maxSurfaces).toBe(1);
  });

  it("provides companion narrative hint for multiple recommendations", () => {
    const cognition = computeAmbientCalmCognition(
      { pendingRecommendations: 5, replayIntegrityDegraded: true },
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    expect(cognition.guidance.narrativeHint).toContain("highest-impact unresolved area");
  });
});

describe("calmComputing", () => {
  it("uses steady-state recovery phrase after stabilization", () => {
    const partnership = computeCognitivePartnership({}, { recentlyResolved: true, confidence: 0.88 });
    const calm = assessCalmComputing({}, partnership, { recentlyResolved: true, confidence: 0.88 });
    expect(calm.recoveryDecompression).toBe(true);
    expect(calm.recoveryPhrase).toContain("steady operational state");
  });
});

describe("operationalErgonomics", () => {
  it("maintains confidence restraint and operational empathy", () => {
    const cognition = computeAmbientCalmCognition({ replayIntegrityDegraded: true }, { confidence: 0.74 });
    expect(cognition.ergonomics.confidenceRestraint).toBe(true);
    expect(cognition.ergonomics.operationalEmpathy).toContain("collaborative prudence");
  });
});

describe("protectedAttention", () => {
  it("resolves invisible attention during deep focus environment", () => {
    expect(
      resolveProtectedAttention({
        mood: "elevated",
        flowState: "immersive",
        recovery: false,
        tension: 0.4,
        deepFocus: true,
      }),
    ).toBe("invisible");
  });

  it("resolves informational attention during investigating flow", () => {
    expect(
      resolveProtectedAttention({
        mood: "informational",
        flowState: "investigating",
        recovery: false,
        tension: 0.3,
      }),
    ).toBe("informational");
  });
});

describe("narrativeCompressionV4", () => {
  it("converges operational complexity into steady reassurance", () => {
    const compressed = compressOperationalEventsV4({
      replayAlertCount: 5,
      telemetryAlertCount: 3,
      recommendationCount: 4,
      recoveryNotices: 1,
      confidenceChanges: 2,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("continues across extended operational sessions");
    expect(compressed[0]).toContain("operational stability remains steady");
  });

  it("integrates calm computing recovery into narrative", () => {
    const cognition = computeAmbientCalmCognition({}, { recentlyResolved: true, confidence: 0.9 });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity",
      confidence: 0.9,
      confidenceLabel: "strong",
      recentlyResolved: true,
      calmComputing: cognition.calmComputing,
      ergonomics: cognition.ergonomics,
    });
    expect(narrative.recoveryStory).toContain("steady operational state");
  });
});

describe("ambientCalmCognition", () => {
  it("orchestrates full ambient cognition stack", () => {
    const cognition = computeAmbientCalmCognition({});
    expect(cognition.partnership).toBeDefined();
    expect(cognition.ambientFlow).toBeDefined();
    expect(cognition.guidance).toBeDefined();
    expect(cognition.calmComputing).toBeDefined();
    expect(cognition.ergonomics).toBeDefined();
    expect(cognition.cognitionClassName).toContain("mc-ambient-flow-sustained");
  });
});
