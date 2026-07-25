import { describe, expect, it } from "vitest";

import { preflightStatusLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("preflightStatusLabels", () => {
  it("maps taxonomy to operator labels", () => {
    const job: TrackedJobRecord = {
      id: "job-1",
      title: "Preflight",
      job_type: "local_workspace_fix_preflight",
      status: "completed",
      params: { preflight_status: "ready_for_approval" },
    };
    expect(preflightStatusLabel(job)).toBe("Preflight ready");
  });

  it("shows needs info label", () => {
    const job: TrackedJobRecord = {
      id: "job-2",
      title: "Env",
      job_type: "vercel_env_var_preflight",
      status: "completed",
      params: { preflight_status: "needs_information" },
    };
    expect(preflightStatusLabel(job)).toBe("Needs info");
  });
});
