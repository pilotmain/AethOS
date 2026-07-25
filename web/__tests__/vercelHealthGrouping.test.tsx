import { describe, expect, it } from "vitest";

import { operationalSummaryFirst } from "@/lib/missionControl/vercelArtifact";

describe("vercelHealthGrouping", () => {
  it("renders healthy and unclear groups separately", () => {
    const summary = operationalSummaryFirst(
      "I found **13** Vercel projects.\n\n**Healthy:**\n- invoicepilot (https://useinvoicepilot.com)\n\n**Production status unclear:**\n- lifeos (production status not confirmed)\n\n**Needs attention:**\n- broken (failed deployment)",
    );
    expect(summary).toContain("Healthy");
    expect(summary).toContain("invoicepilot");
    expect(summary).toContain("Production status unclear");
    expect(summary).not.toContain("All degraded");
  });
});
