import { describe, expect, it } from "vitest";

import {
  executionConfidenceLabel,
  executionEvidenceFromJob,
  executionOperationalEventsFromJob,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("executionEvidenceRendering", () => {
  const job = {
    id: "job-exec1",
    job_type: "readonly_execution_vercel",
    status: "completed",
    params: {
      readonly_execution: {
        provider: "vercel",
        operation_type: "why_down",
        target_name: "talking-avatar-agent",
        confidence: "confirmed",
        probable_root_cause: "Build failed: missing NEXT_PUBLIC_API_URL",
        evidence: [
          {
            source: "vercel_api",
            type: "failure_reason",
            confidence: "confirmed",
            message: "Build failed: missing NEXT_PUBLIC_API_URL",
          },
        ],
        operational_events: [
          { at: "2026-05-20T10:03:00Z", label: "deployment failed", source: "vercel_api" },
        ],
      },
    },
  } as unknown as TrackedJobRecord;

  it("reads structured evidence from readonly execution artifact", () => {
    expect(executionEvidenceFromJob(job)).toHaveLength(1);
    expect(executionEvidenceFromJob(job)[0]?.message).toMatch(/NEXT_PUBLIC_API_URL/);
    expect(executionOperationalEventsFromJob(job)[0]?.label).toBe("deployment failed");
    expect(executionConfidenceLabel(job)).toBe("confirmed");
  });
});
