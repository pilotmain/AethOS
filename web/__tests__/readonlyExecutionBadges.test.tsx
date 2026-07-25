import { describe, expect, it } from "vitest";

import { readonlyExecutionBadge } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("readonlyExecutionBadges", () => {
  it("shows readonly safety badge", () => {
    const job = {
      job_type: "readonly_execution_vercel",
      params: { read_only: true },
    } as unknown as TrackedJobRecord;
    expect(readonlyExecutionBadge(job)).toMatch(/Read-only execution/i);
  });
});
