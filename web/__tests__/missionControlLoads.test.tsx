import { describe, expect, it } from "vitest";

import { formatMcPanelError, mcFailureAffectsChat } from "@/lib/missionControl/panelError";
import { MISSION_CONTROL_TABS, TAB_LABELS, isMissionControlTab } from "@/lib/missionControl/tabs";

describe("missionControlLoads", () => {
  it("exposes Overview, Browser, Jobs, and Settings tabs", () => {
    expect(MISSION_CONTROL_TABS).toEqual(["overview", "browser", "jobs", "settings"]);
    expect(TAB_LABELS.overview).toBe("Overview");
    expect(TAB_LABELS.jobs).toBe("Jobs");
    expect(TAB_LABELS.settings).toBe("Settings");
  });

  it("validates tab ids", () => {
    expect(isMissionControlTab("overview")).toBe(true);
    expect(isMissionControlTab("chat")).toBe(false);
  });

  it("formats panel errors without chat-degraded copy", () => {
    const msg = formatMcPanelError("Panel degraded — other areas may work");
    expect(msg).not.toMatch(/panel degraded/i);
    expect(msg).toMatch(/chat is unaffected/i);
  });

  it("MC failure does not affect chat send state", () => {
    expect(mcFailureAffectsChat("Mission Control request failed: 503")).toBe(false);
  });
});
