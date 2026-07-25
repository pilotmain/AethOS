import { describe, expect, it } from "vitest";

import { computeAmbientPresence } from "@/lib/missionControl/ambientPresence";
import { buildOperationalNarrative } from "@/lib/missionControl/operationalStorytelling";
import { assessQuietIntelligence } from "@/lib/missionControl/quietIntelligence";
import {
  detectSurfaceFocus,
  prioritizeSurfaces,
  shouldShowConnectionHealth,
} from "@/lib/missionControl/surfacePrioritization";

describe("ambientPresence", () => {
  it("defaults to stable calm mood", () => {
    const ambient = computeAmbientPresence({});
    expect(ambient.mood).toBe("stable");
    expect(ambient.rhythm).toBe("calm");
  });

  it("elevates ambient mood for replay integrity concern", () => {
    const ambient = computeAmbientPresence({ replayIntegrityDegraded: true });
    expect(ambient.mood).toBe("elevated");
    expect(ambient.presenceLabel).toContain("Elevated");
  });

  it("softens ambient state in quiet mode", () => {
    const ambient = computeAmbientPresence({ hasActiveJobs: true }, { quietMode: true });
    expect(ambient.rhythm).toBe("calm");
  });
});

describe("surfacePrioritization", () => {
  it("prioritizes replay surfaces when replay integrity is degraded", () => {
    expect(detectSurfaceFocus({ replayIntegrityDegraded: true })).toBe("replay");
    const surfaces = prioritizeSurfaces("operator", { replayIntegrityDegraded: true });
    expect(surfaces.some((s) => s.id === "companion-replay-intelligence")).toBe(true);
  });

  it("hides connection health during executive review", () => {
    expect(shouldShowConnectionHealth("executive", {})).toBe(false);
  });

  it("prioritizes engineering during preflights", () => {
    expect(detectSurfaceFocus({ hasActivePreflights: true })).toBe("engineering");
  });
});

describe("operationalStorytelling", () => {
  it("uses narrative copy instead of telemetry labels", () => {
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity during long-running sessions",
      confidence: 0.72,
      confidenceLabel: "moderate",
      replayDegraded: true,
    });
    expect(narrative.primaryStory).toContain("Replay continuity confidence");
    expect(narrative.companionNote).toContain("highest-impact unresolved area");
    expect(narrative.compressedAlerts[0]).toContain("long-running");
  });
});

describe("quietIntelligence", () => {
  it("suppresses noise in focus mode", () => {
    const quiet = assessQuietIntelligence({ focusMode: true, confidence: 0.8 });
    expect(quiet.suppressQuickLinks).toBe(true);
    expect(quiet.maxVisibleChips).toBe(1);
  });

  it("gates depth when confidence is low", () => {
    const quiet = assessQuietIntelligence({ confidence: 0.48 });
    expect(quiet.depthExpandAllowed).toBe(true);
    expect(quiet.silenceReason).toContain("Confidence gating");
  });
});
