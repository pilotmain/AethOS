import { describe, expect, it } from "vitest";

import { dedupeJobsById } from "@/lib/missionControl/trackedJobs";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("dedupeJobsById", () => {
  it("dedupes by job.id keeping latest updated_at", () => {
    const jobs: TrackedJobRecord[] = [
      { id: "job-a", title: "old", job_type: "mutation_preflight", status: "completed", updated_at: 1 },
      { id: "job-a", title: "new", job_type: "mutation_preflight", status: "completed", updated_at: 9 },
      { id: "job-b", title: "other", job_type: "mutation_execution", status: "completed", updated_at: 2 },
    ] as TrackedJobRecord[];
    const out = dedupeJobsById(jobs);
    expect(out).toHaveLength(2);
    expect(out.find((j) => j.id === "job-a")?.title).toBe("new");
  });
});
