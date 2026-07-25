import { describe, expect, it } from "vitest";

import { isCurrentPreflight, partitionPreflights } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("preflightSupersededRendering", () => {
  it("separates current and superseded preflights", () => {
    const jobs: TrackedJobRecord[] = [
      {
        id: "job-old",
        title: "Old",
        job_type: "vercel_env_var_preflight",
        status: "completed",
        params: { is_current: false, preflight_status: "superseded", superseded_by: "job-new" },
      },
      {
        id: "job-new",
        title: "New",
        job_type: "vercel_env_var_preflight",
        status: "completed",
        params: { is_current: true, preflight_status: "needs_information" },
      },
    ];
    const { current, previous } = partitionPreflights(jobs);
    expect(current).toHaveLength(1);
    expect(previous).toHaveLength(1);
    expect(isCurrentPreflight(jobs[0]!)).toBe(false);
    expect(isCurrentPreflight(jobs[1]!)).toBe(true);
  });
});
