import { describe, expect, it } from "vitest";

import {
  isBrowserUnavailableInformational,
  operationCapabilityFromJob,
  showsApiTokenPreflightPath,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("apiCapableExecutionNoBrowserRequired", () => {
  it("marks API execution jobs as not browser-required", () => {
    const job = {
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        auth_method: "api_token",
        auth_method_label: "Vercel API token",
        api_capable: true,
        browser_runtime_required: false,
        operation_type: "list_domains",
      },
    } as unknown as TrackedJobRecord;
    const cap = operationCapabilityFromJob(job);
    expect(cap.apiCapable).toBe(true);
    expect(cap.browserRequired).toBe(false);
    expect(isBrowserUnavailableInformational(job)).toBe(true);
    expect(showsApiTokenPreflightPath(job)).toBe(true);
  });
});
