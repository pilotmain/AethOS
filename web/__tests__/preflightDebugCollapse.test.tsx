import { describe, expect, it } from "vitest";

import { preflightDebugState } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("preflightDebugCollapse", () => {
  it("extracts debug target resolution fields only", () => {
    const job = {
      id: "job-pf1",
      title: "Preflight",
      job_type: "vercel_domains_preflight",
      status: "completed",
      params: {
        operation_preflight: {
          current_state: {
            api_capable: true,
            credential_id: "cred-1",
            resolution_source: "provider_api",
            production_url: "invoicepilot.vercel.app",
          },
        },
      },
    } as TrackedJobRecord;
    const debug = preflightDebugState(job);
    expect(debug.api_capable).toBe(true);
    expect(debug.resolution_source).toBe("provider_api");
    expect(debug.production_url).toBeUndefined();
  });
});
