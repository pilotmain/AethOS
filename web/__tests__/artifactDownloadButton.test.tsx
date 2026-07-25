import { describe, expect, it } from "vitest";

import { downloadFilename, jobFullReport } from "@/lib/missionControl/jobArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("artifactDownloadButton", () => {
  const job: TrackedJobRecord = {
    id: "job-dl-9",
    title: "Research: Top Competitors",
    job_type: "comparison_brief",
    status: "completed",
    full_result: "# Report\n\n- Item one",
  };

  it("builds a safe markdown filename from title and id", () => {
    const name = downloadFilename(job);
    expect(name).toMatch(/\.md$/);
    expect(name).toContain("job-dl-9");
    expect(name).not.toMatch(/[<>:"/\\|?*]/);
  });

  it("full report text is non-empty for download payload", () => {
    expect(jobFullReport(job)).toContain("# Report");
  });
});
