import { describe, expect, it } from "vitest";

import { assessCognitiveHarmony } from "@/lib/missionControl/cognitiveHarmony";
import { assessCognitiveErgonomics } from "@/lib/missionControl/cognitiveErgonomics";
import { assessFlowProtection } from "@/lib/missionControl/flowProtection";
import {
  assessOperationalConsciousness,
  computeOperationalConsciousness,
} from "@/lib/missionControl/operationalConsciousness";
import { computeAmbientCalmCognition } from "@/lib/missionControl/ambientCognitiveFlow";
import {
  buildOperationalNarrative,
  compressOperationalEventsV5,
} from "@/lib/missionControl/operationalStorytelling";
import { resolveHarmoniousAttention } from "@/lib/missionControl/spatialHierarchy";

describe("operationalConsciousness", () => {
  it("protects cognition during extended investigation", () => {
    const ops = computeOperationalConsciousness(
      { replayIntegrityDegraded: true, hasActiveJobs: true, pendingRecommendations: 6 },
      { focusMode: true, priorityIssue: "replay continuity validation" },
    );
    expect(ops.consciousness.cognitiveProtection).toBe(true);
    expect(ops.consciousness.immersionPreservation).toBe(true);
    expect(ops.flowProtection.interruptionPrevented).toBe(true);
    expect(ops.deepImmersion).toBe(true);
  });

  it("preserves awareness continuity under replay pressure", () => {
    const ops = computeOperationalConsciousness({ replayIntegrityDegraded: true });
    expect(ops.consciousness.consciousnessState).toBe("focused");
    expect(ops.consciousness.awarenessContinuity).toBe(true);
  });

  it("enters restoring consciousness after stabilization", () => {
    const cognition = computeAmbientCalmCognition({}, { recentlyResolved: true, confidence: 0.9 });
    const field = assessOperationalConsciousness({}, cognition, { recentlyResolved: true });
    expect(field.consciousnessState).toBe("restoring");
  });
});

describe("flowProtection", () => {
  it("shields noise and suppresses recommendations in deep immersion", () => {
    const ops = computeOperationalConsciousness({ replayIntegrityDegraded: true, pendingRecommendations: 6 }, { focusMode: true });
    expect(ops.flowProtection.noiseShielded).toBe(true);
    expect(ops.flowProtection.recommendationsSuppressed).toBe(true);
    expect(ops.flowProtection.maxSurfaces).toBe(1);
    expect(ops.flowProtection.hidePeripheralChrome).toBe(true);
  });
});

describe("cognitiveHarmony", () => {
  it("communicates steady operational rhythm after recovery", () => {
    const cognition = computeAmbientCalmCognition({}, { recentlyResolved: true, confidence: 0.88 });
    const harmony = assessCognitiveHarmony({}, cognition, { recentlyResolved: true, confidence: 0.88 });
    expect(harmony.recoveryAtmosphere).toBe(true);
    expect(harmony.recoveryPhrase).toContain("steady operational rhythm");
  });
});

describe("cognitiveErgonomics", () => {
  it("compresses multiple alerts into companion phrase", () => {
    const ops = computeOperationalConsciousness(
      { pendingRecommendations: 6, replayIntegrityDegraded: true },
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    expect(ops.cognitiveErgonomics.companionPhrase).toContain("highest-impact unresolved area");
    expect(ops.cognitiveErgonomics.confidenceRestraint).toBe(true);
  });
});

describe("harmoniousAttention", () => {
  it("resolves invisible attention during deep immersion", () => {
    expect(
      resolveHarmoniousAttention({
        mood: "elevated",
        consciousnessState: "immersive",
        recovery: false,
        tension: 0.4,
        deepImmersion: true,
      }),
    ).toBe("invisible");
  });

  it("resolves atmospheric attention during aware state", () => {
    expect(
      resolveHarmoniousAttention({
        mood: "informational",
        consciousnessState: "aware",
        recovery: false,
        tension: 0.2,
      }),
    ).toBe("atmospheric");
  });
});

describe("narrativeCompressionV5", () => {
  it("converges operational complexity with broader stability reassurance", () => {
    const compressed = compressOperationalEventsV5({
      replayAlertCount: 6,
      telemetryAlertCount: 3,
      recommendationCount: 4,
      recoveryNotices: 1,
      confidenceChanges: 2,
      confidenceWarnings: 1,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("persists across extended operational sessions");
    expect(compressed[0]).toContain("broader operational stability remains steady");
  });

  it("integrates harmony recovery into narrative", () => {
    const ops = computeOperationalConsciousness({}, { recentlyResolved: true, confidence: 0.9 });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity",
      confidence: 0.9,
      confidenceLabel: "strong",
      recentlyResolved: true,
      harmony: ops.harmony,
      cognitiveErgonomics: ops.cognitiveErgonomics,
    });
    expect(narrative.recoveryStory).toContain("steady operational rhythm");
  });
});

describe("calmOperationalConsciousness", () => {
  it("orchestrates full consciousness stack", () => {
    const ops = computeOperationalConsciousness({});
    expect(ops.cognition).toBeDefined();
    expect(ops.consciousness).toBeDefined();
    expect(ops.flowProtection).toBeDefined();
    expect(ops.harmony).toBeDefined();
    expect(ops.cognitiveErgonomics).toBeDefined();
    expect(ops.consciousnessClassName).toContain("mc-consciousness-");
  });
});
