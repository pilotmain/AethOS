import { describe, expect, it } from "vitest";

import {
  partitionGroupedJobs,
  readonlyExecutionsEmpty,
} from "@/lib/missionControl/operationPreflight";
import { emptyJobsGrouped } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionsSection", () => {
  it("partitions readonly execution jobs into dedicated buckets", () => {
    const grouped = {
      ...emptyJobsGrouped(),
      completed: [
        {
          id: "job-pf",
          title: "Preflight",
          job_type: "vercel_domains_preflight",
          status: "completed",
        },
        {
          id: "job-ex",
          title: "Read-only execution",
          job_type: "readonly_execution_vercel",
          status: "completed",
          params: { operation_type: "list_domains" },
        },
      ],
      running: [
        {
          id: "job-run",
          title: "Running execution",
          job_type: "readonly_execution_vercel",
          status: "running",
        },
      ],
    };
    const { readonlyExecutions, withoutReadonlyExecutions } = partitionGroupedJobs(grouped);
    expect(readonlyExecutions.completed).toHaveLength(1);
    expect(readonlyExecutions.running).toHaveLength(1);
    expect(withoutReadonlyExecutions.completed).toHaveLength(1);
    expect(readonlyExecutionsEmpty(readonlyExecutions)).toBe(false);
  });
});
