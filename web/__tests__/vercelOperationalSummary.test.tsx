import { describe, expect, it } from "vitest";

import { operationalSummaryFirst } from "@/lib/missionControl/vercelArtifact";

describe("vercelOperationalSummary", () => {
  it("prefers human operational summary text", () => {
    const summary =
      "I found **8** Vercel projects.\n\n**Healthy:**\n- invoicepilot\n\n**Needs attention:**\n- lifeos (no production deployment)";
    expect(operationalSummaryFirst(summary)).toContain("Vercel projects");
    expect(operationalSummaryFirst(summary)).toContain("Healthy");
    expect(operationalSummaryFirst(summary)).not.toContain("Hobby");
  });
});
