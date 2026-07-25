import { describe, expect, it } from "vitest";

import { splitFullReportSections } from "@/lib/missionControl/vercelArtifact";

describe("artifactRawDebugCollapsed", () => {
  it("splits debug extraction into collapsible section", () => {
    const full = "# Report\n\n## Structured project inventory\n\n| a |\n\n## Debug extraction\n\n```\nraw\n```";
    const { main, debug } = splitFullReportSections(full);
    expect(main).toContain("Structured project inventory");
    expect(main).not.toContain("raw");
    expect(debug).toContain("Debug extraction");
    expect(debug).toContain("raw");
  });

  it("returns main only when no debug marker", () => {
    const { main, debug } = splitFullReportSections("# Only structured\n\n- app");
    expect(main).toContain("structured");
    expect(debug).toBeNull();
  });
});
