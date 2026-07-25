import { describe, expect, it } from "vitest";

import {
  canApproveReadonlyExecution,
  isBrowserUnavailableInformational,
  showsApiTokenPreflightPath,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("apiFirstPreflightNotBlockedByBrowser", () => {
  it("allows approval for API-capable domain preflight", () => {
    const job = {
      id: "job-domains",
      job_type: "vercel_domains_preflight",
      status: "completed",
      params: {
        preflight_status: "ready_for_approval",
        is_current: true,
        operation_preflight: {
          operation_type: "list_domains",
          provider: "vercel",
          current_state: {
            api_capable: true,
            auth_method: "api_token",
            browser_runtime_required: false,
          },
        },
      },
    } as unknown as TrackedJobRecord;
    expect(showsApiTokenPreflightPath(job)).toBe(true);
    expect(isBrowserUnavailableInformational(job)).toBe(true);
    expect(canApproveReadonlyExecution(job)).toBe(true);
  });
});
