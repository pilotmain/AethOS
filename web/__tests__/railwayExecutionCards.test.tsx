import { describe, expect, it } from "vitest";

import { readonlyExecutionCardMeta } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("railwayExecutionCards", () => {
  it("renders railway execution metadata without provider-specific branches", () => {
    const job: TrackedJobRecord = {
      id: "job-rw-1",
      title: "Read-only execution — why down (api-worker)",
      job_type: "readonly_execution",
      status: "completed",
      created_at: 1,
      updated_at: 2,
      params: {
        provider: "railway",
        operation_type: "why_down",
        target_name: "api-worker",
        auth_method: "api_token",
        auth_method_label: "Railway API token",
        data_source: "provider_api",
        readonly_execution: {
          provider: "railway",
          operation_type: "why_down",
          target_name: "api-worker",
          auth_method_label: "Railway API token",
          data_source: "provider_api",
          evidence: [{ source: "railway_api", type: "deployment", confidence: "confirmed", message: "failed" }],
          operational_events: [],
          timeline: [],
        },
      },
      result: "",
      full_result: "",
    };
    const meta = readonlyExecutionCardMeta(job);
    expect(meta.provider).toBe("railway");
    expect(meta.operation).toBe("why down");
    expect(meta.target).toBe("api-worker");
    expect(meta.authMethod).toBe("Railway API token");
    expect(meta.dataSource).toBe("Provider API execution");
  });
});
