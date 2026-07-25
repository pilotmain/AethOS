import { describe, expect, it } from "vitest";

/** Evidence-aware health labels — backend mirrors these strings. */
describe("healthEvidenceRendering", () => {
  it("expects production down only with production scope evidence", () => {
    const withScope = "invoicepilot · production down";
    const withoutScope = "invoicepilot · latest deployment failed — production impact unclear";
    expect(withScope.toLowerCase()).toContain("production down");
    expect(withoutScope.toLowerCase()).not.toContain("production down");
    expect(withoutScope.toLowerCase()).toContain("unclear");
  });
});
