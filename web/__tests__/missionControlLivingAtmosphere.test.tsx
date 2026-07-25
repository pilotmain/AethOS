import { describe, expect, it } from "vitest";

import { computeOperationalEnvironment } from "@/lib/missionControl/environmentalIntelligence";
import { assessEmotionalPacing } from "@/lib/missionControl/emotionalPacing";
import { deriveLivingRhythm, rhythmClassNames } from "@/lib/missionControl/livingRhythm";
import { buildOperationalNarrative } from "@/lib/missionControl/operationalStorytelling";
import { dominantAttentionLevel } from "@/lib/missionControl/spatialHierarchy";

describe("environmentalIntelligence", () => {
  it("returns cool-quiet atmosphere for stable context", () => {
    const env = computeOperationalEnvironment({});
    expect(env.atmosphere).toBe("cool-quiet");
    expect(env.atmosphereWhisper).toContain("breathable");
    expect(env.shellClassName).toContain("mc-atmosphere-cool-quiet");
  });

  it("warms atmosphere for replay integrity concern", () => {
    const env = computeOperationalEnvironment({ replayIntegrityDegraded: true });
    expect(env.atmosphere).toBe("warm-focus");
    expect(env.mood).toBe("elevated");
    expect(env.rhythm.expandActiveInvestigation).toBe(true);
  });

  it("enters recovery calming after resolution", () => {
    const env = computeOperationalEnvironment({}, { recentlyResolved: true, confidence: 0.86 });
    expect(env.pacing.recoveryCalming).toBe(true);
    expect(env.pacing.suppressUrgencyStacking).toBe(true);
    expect(env.atmosphereWhisper).toContain("returning to a stable state");
  });

  it("uses restrained urgency only for critical instability", () => {
    const env = computeOperationalEnvironment({
      hasAnomalies: true,
      replayIntegrityDegraded: true,
    }, { confidence: 0.42 });
    expect(env.atmosphere).toBe("restrained-urgency");
    expect(env.attentionLevel).toBe("urgent");
  });
});

describe("emotionalPacing", () => {
  it("suppresses urgency stacking in quiet confidence", () => {
    const pacing = assessEmotionalPacing({}, { confidence: 0.88, recentlyResolved: true });
    expect(pacing.tension).toBeLessThan(0.2);
    expect(pacing.suppressUrgencyStacking).toBe(true);
    expect(pacing.recoveryCalming).toBe(true);
  });

  it("escalates gradually rather than jumping to critical", () => {
    const pacing = assessEmotionalPacing({ replayIntegrityDegraded: true });
    expect(pacing.escalation).toBe("gradual");
    expect(pacing.tension).toBeGreaterThan(0.3);
    expect(pacing.tension).toBeLessThan(0.75);
  });

  it("caps tension in focus mode", () => {
    const pacing = assessEmotionalPacing(
      { hasAnomalies: true, replayIntegrityDegraded: true },
      { focusMode: true },
    );
    expect(pacing.tension).toBeLessThanOrEqual(0.45);
    expect(pacing.focusPreservation).toBe(true);
  });
});

describe("livingRhythm", () => {
  it("slows tempo during recovery calming", () => {
    const pacing = assessEmotionalPacing({}, { recentlyResolved: true, confidence: 0.9 });
    const rhythm = deriveLivingRhythm("stable", pacing, { quietMode: true });
    expect(rhythm.tempo).toBe("slow");
    expect(rhythm.breathe).toBe(true);
    expect(rhythm.compressInactive).toBe(true);
  });

  it("emits rhythm class names for atmospheric motion", () => {
    const rhythm = deriveLivingRhythm("elevated", assessEmotionalPacing({ replayIntegrityDegraded: true }));
    const classes = rhythmClassNames(rhythm);
    expect(classes).toContain("mc-ambient-pulse");
    expect(classes).toContain("mc-expand-investigation");
  });
});

describe("operationalStorytelling — companion 2.0", () => {
  it("communicates narrative recovery instead of telemetry", () => {
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity during long-running sessions",
      confidence: 0.86,
      confidenceLabel: "high",
      recentlyResolved: true,
    });
    expect(narrative.recoveryStory).toContain("calm operational rhythm");
    expect(narrative.companionHeadline).toContain("highest-impact unresolved area");
  });

  it("compresses pending recommendations into calm copy", () => {
    const narrative = buildOperationalNarrative({
      priorityIssue: "runtime integrity validation",
      confidence: 0.7,
      confidenceLabel: "moderate",
      pendingRecommendations: 3,
    });
    expect(narrative.compressedAlerts[0]).toContain("grouped for clarity");
  });
});

describe("spatialHierarchy — ultra-calm attention", () => {
  it("resolves a single dominant attention level", () => {
    expect(dominantAttentionLevel(["passive", "contextual", "informational"])).toBe("contextual");
    expect(dominantAttentionLevel(["passive", "critical", "elevated"])).toBe("critical");
  });
});
