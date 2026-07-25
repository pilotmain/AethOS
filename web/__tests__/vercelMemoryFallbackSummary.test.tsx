import { describe, expect, it } from "vitest";

import { isUsefulEmptyExtractionSummary, operationalSummaryFirst } from "@/lib/missionControl/vercelArtifact";

describe("vercelMemoryFallbackSummary", () => {
  it("shows memory fallback as useful operator text", () => {
    const summary = operationalSummaryFirst(
      "I could not confidently re-extract projects from the current Vercel page, but I have **3** previously confirmed projects in memory:\n\n- invoicepilot",
    );
    expect(summary).toContain("memory");
    expect(summary).toContain("invoicepilot");
    expect(isUsefulEmptyExtractionSummary(summary)).toBe(true);
    expect(summary.toLowerCase()).not.toContain("found 0 vercel projects");
  });
});
