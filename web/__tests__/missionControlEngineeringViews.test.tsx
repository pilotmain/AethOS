import { describe, expect, it } from "vitest";

import { SIDEBAR_SECTIONS, viewDataGroup } from "@/lib/missionControl/views";

describe("missionControlEngineeringViews", () => {
  it("includes Engineering sidebar section", () => {
    const engineering = SIDEBAR_SECTIONS.find((s) => s.title === "Engineering");
    expect(engineering).toBeDefined();
    expect(engineering?.items.map((i) => i.id)).toContain("local-workspaces");
    expect(engineering?.items.map((i) => i.id)).toContain("pr-proposals");
  });

  it("maps engineering views to engineering data group", () => {
    expect(viewDataGroup("local-workspaces")).toBe("engineering");
    expect(viewDataGroup("architecture-maps")).toBe("engineering");
    expect(viewDataGroup("git-activity")).toBe("engineering");
    expect(viewDataGroup("overview")).toBe("overview");
  });
});
