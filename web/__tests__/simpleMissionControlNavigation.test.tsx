import { describe, expect, it } from "vitest";

import {
  ADVANCED_SETTINGS_VIEW_IDS,
  FLAT_NAV_GROUPS,
  flatNavRedirectForView,
  isMainNavView,
  MAIN_NAV_VIEW_IDS,
  MERGED_INTO_PRIMARY,
} from "@/lib/missionControl/flatNavigation";

describe("flatMissionControlNavigation", () => {
  it("exposes grouped flat nav destinations", () => {
    expect(FLAT_NAV_GROUPS.length).toBeGreaterThanOrEqual(4);
    expect(MAIN_NAV_VIEW_IDS.has("overview")).toBe(true);
    expect(MAIN_NAV_VIEW_IDS.has("agent-orchestration")).toBe(true);
    expect(MAIN_NAV_VIEW_IDS.has("settings")).toBe(true);
    expect(MAIN_NAV_VIEW_IDS.has("cross-lane-operations")).toBe(false);
  });

  it("recognizes main nav views", () => {
    expect(isMainNavView("overview")).toBe(true);
    expect(isMainNavView("workflow-operations")).toBe(false);
    expect(isMainNavView("integrity-diagnostics")).toBe(false);
  });

  it("lists advanced settings separately from main nav", () => {
    expect(ADVANCED_SETTINGS_VIEW_IDS.has("integrity-diagnostics")).toBe(true);
    expect(ADVANCED_SETTINGS_VIEW_IDS.has("overview")).toBe(false);
  });

  it("merges duplicate approval surfaces into Approvals", () => {
    for (const [from, to] of Object.entries(MERGED_INTO_PRIMARY)) {
      if (to === "approval-inbox") {
        expect(flatNavRedirectForView(from as never)).toBe("approval-inbox");
      }
    }
    expect(flatNavRedirectForView("overview")).toBe("overview");
  });
});
