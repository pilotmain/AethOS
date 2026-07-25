import { describe, expect, it } from "vitest";

import {
  buildMissionControlUrl,
  buildResearchReplayUrl,
  MC_DEEP_LINKS,
  missionControlHref,
  REPLAY_PARAM,
} from "@/lib/missionControl/deepLinks";
import { isSimpleNavView } from "@/lib/missionControl/simpleNavigation";

describe("missionControl deepLinks", () => {
  it("builds mc_view query URLs", () => {
    expect(buildMissionControlUrl("deep-research")).toBe("/mission-control?mc_view=deep-research");
    expect(missionControlHref("agents")).toBe("/mission-control?mc_view=agent-orchestration");
    expect(missionControlHref("approvals")).toContain("approval-inbox");
  });

  it("builds research replay deep links", () => {
    expect(buildResearchReplayUrl("rrun-abc123")).toBe(
      `/mission-control?mc_view=deep-research&${REPLAY_PARAM}=rrun-abc123`,
    );
    expect(buildResearchReplayUrl("")).toBe("/mission-control?mc_view=deep-research");
  });

  // FIX 2 — tool panels advertised in the Chat sidebar must be reachable in
  // simple nav, otherwise the simple-nav guard force-redirects them to Home.
  it("keeps deep-linked tool panels reachable in simple nav", () => {
    expect(isSimpleNavView("evidence-gallery")).toBe(true);
    expect(isSimpleNavView("research-library")).toBe(true);
    expect(isSimpleNavView("mcp-bridge")).toBe(true);
    expect(isSimpleNavView("blind-model-eval")).toBe(true);
  });

  it("every Chat-sidebar TOOLS deep link resolves to a simple-nav-reachable view", () => {
    for (const key of ["research", "gallery", "library", "agents", "approvals", "jobs", "mcp"] as const) {
      expect(isSimpleNavView(MC_DEEP_LINKS[key])).toBe(true);
    }
  });
});
