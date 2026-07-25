import { describe, expect, it } from "vitest";

import {
  assessCognitivePresence,
  computeCognitiveOperationalPresence,
  resolveDominantThought,
} from "@/lib/missionControl/cognitivePresence";
import { computeOperationalEnvironment } from "@/lib/missionControl/environmentalIntelligence";
import { assessEmotionalTrust } from "@/lib/missionControl/emotionalTrust";
import { assessInvisibleIntelligence } from "@/lib/missionControl/invisibleIntelligence";
import {
  buildOperationalNarrative,
  compressOperationalEvents,
} from "@/lib/missionControl/operationalStorytelling";
import { assessSpatialTrust } from "@/lib/missionControl/spatialTrust";

describe("cognitivePresence", () => {
  it("estimates elevated load under operational pressure", () => {
    const env = computeOperationalEnvironment({
      hasAnomalies: true,
      replayIntegrityDegraded: true,
      hasActiveJobs: true,
    });
    const cognitive = assessCognitivePresence(
      { hasAnomalies: true, replayIntegrityDegraded: true, hasActiveJobs: true },
      env,
    );
    expect(cognitive.loadLevel).toBe("heavy");
    expect(cognitive.suppressSecondaryChrome).toBe(true);
    expect(cognitive.expandInvestigationOnly).toBe(true);
  });

  it("reduces load in deep focus mode", () => {
    const presence = computeCognitiveOperationalPresence(
      { hasAnomalies: true, replayIntegrityDegraded: true },
      { focusMode: true },
    );
    expect(presence.deepFocusActive).toBe(true);
    expect(presence.cognitive.loadLevel).not.toBe("heavy");
    expect(presence.invisible.maxSurfaces).toBe(2);
  });

  it("returns no dominant thought during recovery", () => {
    const env = computeOperationalEnvironment({}, { recentlyResolved: true, confidence: 0.88 });
    const cognitive = assessCognitivePresence({}, env, { recentlyResolved: true });
    expect(resolveDominantThought({}, cognitive, env, { recentlyResolved: true })).toBeNull();
  });

  it("surfaces singular dominant thought during critical load", () => {
    const presence = computeCognitiveOperationalPresence(
      { hasAnomalies: true, replayIntegrityDegraded: true },
      { confidence: 0.4, priorityIssue: "replay continuity validation" },
    );
    expect(presence.dominantThought).toContain("Singular focus");
  });
});

describe("invisibleIntelligence", () => {
  it("suppresses weak recommendations under fatigue", () => {
    const env = computeOperationalEnvironment({ replayIntegrityDegraded: true, hasActiveJobs: true });
    const cognitive = assessCognitivePresence({ replayIntegrityDegraded: true, hasActiveJobs: true }, env);
    const invisible = assessInvisibleIntelligence({ replayIntegrityDegraded: true, hasActiveJobs: true }, cognitive, {
      focusMode: true,
    });
    expect(invisible.suppressWeakRecommendations).toBe(true);
    expect(invisible.batchRecommendations).toBe(true);
    expect(invisible.smartQuietState).toBe(true);
  });

  it("limits surfaces during adaptive simplification", () => {
    const env = computeOperationalEnvironment({ hasActivePreflights: true });
    const cognitive = assessCognitivePresence({ hasActivePreflights: true }, env);
    const invisible = assessInvisibleIntelligence({ hasActivePreflights: true }, cognitive, { quietMode: true });
    expect(invisible.maxSurfaces).toBeLessThanOrEqual(3);
    expect(invisible.adaptiveSimplification).toBe(true);
  });
});

describe("spatialTrust", () => {
  it("signals calm recovery transition", () => {
    const env = computeOperationalEnvironment({}, { recentlyResolved: true, confidence: 0.86 });
    const trust = assessSpatialTrust({}, env, { recentlyResolved: true, confidence: 0.86 });
    expect(trust.recoveryTransition).toBe(true);
    expect(trust.trustWhisper).toContain("settling");
  });

  it("applies visual restraint during uncertainty", () => {
    const env = computeOperationalEnvironment({ replayIntegrityDegraded: true });
    const trust = assessSpatialTrust({ replayIntegrityDegraded: true }, env, { confidence: 0.68 });
    expect(trust.visualRestraint).toBe(true);
    expect(trust.confidenceEmphasis).toBe("restrained");
  });
});

describe("emotionalTrust", () => {
  it("avoids overclaiming when replay is degraded", () => {
    const trust = assessEmotionalTrust({ replayIntegrityDegraded: true }, {
      confidence: 0.82,
      confidenceLabel: "strong",
      replayDegraded: true,
    });
    expect(trust.suppressOverclaiming).toBe(true);
    expect(trust.confidencePhrase).toContain("extended-session validation");
    expect(trust.confidencePhrase).not.toContain("High confidence");
  });

  it("uses grounded stability phrasing after recovery", () => {
    const trust = assessEmotionalTrust({}, {
      confidence: 0.86,
      confidenceLabel: "strong",
      recentlyResolved: true,
    });
    expect(trust.stabilityPhrase).toContain("long-session validation");
  });
});

describe("narrativeCompression", () => {
  it("compresses repetitive replay alerts into one narrative", () => {
    const compressed = compressOperationalEvents({
      replayAlertCount: 5,
      telemetryAlertCount: 3,
      recommendationCount: 4,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("persists across extended operational sessions");
  });

  it("integrates emotional trust into operational narrative", () => {
    const trust = assessEmotionalTrust({ replayIntegrityDegraded: true }, {
      confidence: 0.75,
      confidenceLabel: "moderate",
      replayDegraded: true,
    });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity",
      confidence: 0.75,
      confidenceLabel: "moderate",
      replayDegraded: true,
      emotionalTrust: trust,
      compression: { replayAlertCount: 5, recommendationCount: 3 },
    });
    expect(narrative.primaryStory).toContain("extended-session validation");
    expect(narrative.compressedAlerts[0]).toContain("persists across extended operational sessions");
  });
});
