import { describe, expect, it } from "vitest";

import { artifactReportPreStyle } from "@/lib/missionControl/layout";
import {
  downloadFilename,
  jobFullReport,
} from "@/lib/missionControl/jobArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("jobsArtifactPanelLayout", () => {
  const longReport =
    "# Competitor brief\n\n" +
    Array.from({ length: 60 }, (_, i) => `- Finding ${i}: detail line\n`).join("");

  const job: TrackedJobRecord = {
    id: "job-scroll-1",
    title: "Competitors",
    job_type: "comparison_brief",
    status: "completed",
    full_result: longReport,
    result_preview: "LangGraph leads agent runtimes",
    result_summary: "- LangGraph\n- CrewAI",
  };

  it("keeps long artifact text in full_result for page-level scroll", () => {
    const full = jobFullReport(job);
    expect(full.length).toBeGreaterThan(1000);
    expect(full.split("\n").length).toBeGreaterThan(50);
  });

  it("artifact pre style allows natural document flow (no max-height clip)", () => {
    expect(artifactReportPreStyle.whiteSpace).toBe("pre-wrap");
    expect("maxHeight" in artifactReportPreStyle).toBe(false);
  });

  it("download filename remains stable for expanded artifacts", () => {
    expect(downloadFilename(job)).toMatch(/competitors-job-scroll-1\.md$/);
  });
});
