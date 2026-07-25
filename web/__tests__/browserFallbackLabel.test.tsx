import { describe, expect, it } from "vitest";

import { executionDataSourceLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("browserFallbackLabel", () => {
  it("shows browser fallback label when API data missing", () => {
    const job = {
      job_type: "readonly_execution_vercel",
      params: { data_source: "browser_fallback" },
    } as unknown as TrackedJobRecord;
    expect(executionDataSourceLabel(job)).toMatch(/Browser fallback/i);
  });
});
