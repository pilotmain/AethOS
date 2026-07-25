import { describe, expect, it } from "vitest";

import {
  buildFocusCanvasState,
  contentForDepth,
  depthLabel,
  quickViewsForMode,
  showConnectionHealth,
  showMetricStrip,
} from "@/lib/missionControl/focusCanvas";
import {
  domainAttentionLevel,
  shouldDimDomain,
  suggestExpandedDomain,
} from "@/lib/missionControl/sidebarIntelligence";
import { confidenceLabel } from "@/lib/missionControl/spatialHierarchy";
import { NAV_DOMAINS } from "@/lib/missionControl/sidebarNavigation";

describe("focusCanvas", () => {
  it("builds companion presence headline from partner brief", () => {
    const state = buildFocusCanvasState(
      {
        remaining_risk: "replay continuity during long-running sessions",
        confidence: 0.72,
        brief: "Summary paragraph.\n\nMore detail.",
        operational_reasoning: { synthesis: "Telemetry degraded after convergence." },
        deep_replay: { compressed_summary: "Integrity 0.61", investigation_branches: ["Validate sessions"] },
      },
      { metrics: { trust_retention: 0.84 }, overall_score: 0.86 },
    );
    expect(state.headline).toContain("most important unresolved issue");
    expect(state.headline).toContain("replay continuity");
    expect(state.confidenceLabel).toBe("moderate");
  });

  it("progressive depth unfolds gradually", () => {
    const state = buildFocusCanvasState(
      {
        brief: "Initial summary.\n\nSecond block.",
        operational_reasoning: { synthesis: "Reasoning layer." },
        deep_replay: { compressed_summary: "Replay layer." },
      },
      null,
    );
    expect(contentForDepth(state, 0)).toBe(state.summary);
    expect(contentForDepth(state, 1)).toContain("Reasoning layer");
    expect(contentForDepth(state, 2)).toContain("Replay layer");
    expect(depthLabel(0)).toBe("Show replay reasoning");
    expect(depthLabel(3)).toBeNull();
  });

  it("adapts quick views and density by mode", () => {
    expect(quickViewsForMode("executive")).toHaveLength(3);
    expect(showMetricStrip("executive")).toBe(false);
    expect(showConnectionHealth("executive")).toBe(false);
    expect(quickViewsForMode("deep-engineering").some((v) => v.id === "integrity-routes")).toBe(true);
  });
});

describe("sidebarIntelligence", () => {
  it("suggests intelligence when replay integrity is degraded", () => {
    expect(suggestExpandedDomain({ replayIntegrityDegraded: true })).toBe("intelligence");
  });

  it("dims passive domains outside active focus", () => {
    const infra = NAV_DOMAINS.find((surface) => surface.id === "infrastructure")!;
    expect(
      shouldDimDomain(infra, "intelligence", { replayIntegrityDegraded: true }, false),
    ).toBe(true);
  });

  it("uses restrained attention levels", () => {
    const ops = NAV_DOMAINS.find((d) => d.id === "operations")!;
    expect(domainAttentionLevel(ops, { hasAnomalies: true })).toBe("urgent");
    expect(domainAttentionLevel(ops, {})).toBe("passive");
  });
});

describe("spatialHierarchy", () => {
  it("maps confidence to calm labels", () => {
    expect(confidenceLabel(0.82)).toBe("strong");
    expect(confidenceLabel(0.68)).toBe("moderate");
  });
});
