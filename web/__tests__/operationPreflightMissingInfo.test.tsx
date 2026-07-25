import { describe, expect, it } from "vitest";

import { missingInfoQuestions } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("operationPreflightMissingInfo", () => {
  it("surfaces env value and environment questions", () => {
    const job: TrackedJobRecord = {
      id: "job-env",
      title: "Env preflight",
      job_type: "vercel_env_var_preflight",
      status: "completed",
      params: {
        operation_preflight: {
          missing_information: ["exact_env_value_confirmation", "environment_target"],
        },
      },
    };
    const q = missingInfoQuestions(job);
    expect(q.some((line) => /env value/i.test(line))).toBe(true);
    expect(q.some((line) => /Production/i.test(line))).toBe(true);
  });
});
