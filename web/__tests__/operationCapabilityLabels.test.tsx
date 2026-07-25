import { describe, expect, it } from "vitest";

import { operationCapabilityFromJob } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("operationCapabilityLabels", () => {
  it("exposes API token capability metadata", () => {
    const job = {
      job_type: "vercel_deployments_preflight",
      status: "completed",
      params: {
        operation_preflight: {
          current_state: {
            api_capable: true,
            auth_method: "api_token",
            browser_runtime_required: false,
          },
        },
      },
    } as unknown as TrackedJobRecord;
    const cap = operationCapabilityFromJob(job);
    expect(cap.apiCapable).toBe(true);
    expect(cap.browserRequired).toBe(false);
    expect(cap.authMethod).toBe("api_token");
  });
});
