import { describe, expect, it } from "vitest";

import { productionImpactLabel } from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("productionImpactConfidenceRendering", () => {
  it("shows production impact confidence separately", () => {
    const job = {
      id: "job-ex",
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        readonly_execution: {
          diagnostic: {
            failure_reason_confidence: "confirmed",
            production_impact_confidence: "insufficient_evidence",
            production_impact_summary: "Unclear — failed deployment target is unknown",
          },
        },
      },
    } as unknown as TrackedJobRecord;
    expect(productionImpactLabel(job)).toBe("insufficient evidence");
  });
});
