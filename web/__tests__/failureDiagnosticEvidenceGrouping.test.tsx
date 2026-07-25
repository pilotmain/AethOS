import { describe, expect, it } from "vitest";

import { executionEvidenceByTier } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("failureDiagnosticEvidenceGrouping", () => {
  it("reads tiered evidence from diagnostic artifact", () => {
    const job = {
      id: "job-ex",
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        readonly_execution: {
          operation_type: "why_down",
          diagnostic: {
            evidence_by_tier: {
              primary: [{ type: "failure_reason", message: "npm run build exited with 1" }],
              debug: [{ type: "deployment_state", message: "old ready deployment" }],
            },
          },
        },
      },
    } as unknown as TrackedJobRecord;
    const tiers = executionEvidenceByTier(job);
    expect(tiers.primary).toHaveLength(1);
    expect(tiers.debug).toHaveLength(1);
  });
});
