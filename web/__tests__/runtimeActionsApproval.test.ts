import { describe, expect, it } from "vitest";

describe("runtimeActionsApprovalSurface", () => {
  it("Approvals is the operator-visible approval surface", async () => {
    const { resolveVisibleNavigationPath } = await import("@/lib/missionControl/visibleNavigationRegistry");
    expect(resolveVisibleNavigationPath("Operation Preflights", "operator")).toBe(
      "Mission Control → Approvals",
    );
  });

  it("runtime actions panel composes preflights and actions modules", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const source = fs.readFileSync(
      path.join(process.cwd(), "components/missionControl/RuntimeActionsPanel.tsx"),
      "utf8",
    );
    expect(source).toContain("JobsTrackedWorkPanel");
    expect(source).toContain('mode="all"');
    expect(source).toContain("JobsActionsPanel");
    expect(source).not.toMatch(/Validation Center|Webhook Truth/);
  });
});
