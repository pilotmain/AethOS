import { describe, expect, it } from "vitest";

import {
  isBareZeroProjectSummary,
  isUsefulEmptyExtractionSummary,
  splitFullReportSections,
} from "@/lib/missionControl/vercelArtifact";

describe("vercelEmptyExtractionArtifact", () => {
  it("detects bare zero-project chat bullets", () => {
    expect(isBareZeroProjectSummary("- Found 0 Vercel projects")).toBe(true);
    expect(isBareZeroProjectSummary("- Could not identify Vercel projects on this page")).toBe(false);
  });

  it("accepts useful empty extraction summaries", () => {
    const summary =
      "I reached the Vercel dashboard, but I could not confidently identify project cards on this page.";
    expect(isUsefulEmptyExtractionSummary(summary)).toBe(true);
  });

  it("splits extraction debug section for collapsed MC display", () => {
    const full = "# Report\n\n## Extraction debug\n\n```json\n{}\n```\n\n## Debug extraction\n\nraw";
    const { main, extractionDebug, debug } = splitFullReportSections(full);
    expect(main).toContain("# Report");
    expect(extractionDebug).toContain("Extraction debug");
    expect(debug == null || debug.includes("Debug extraction")).toBe(true);
  });
});
