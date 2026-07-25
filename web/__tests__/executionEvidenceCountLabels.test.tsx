import { describe, expect, it } from "vitest";

import {
  executionEvidenceSummary,
  formatExecutionDebugEvidenceLabel,
  formatExecutionEvidenceLabel,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("executionEvidenceCountLabels", () => {
  it("shows tiered counts instead of flat total for failure diagnostics", () => {
    const job = {
      id: "job-ex",
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        readonly_execution: {
          evidence: Array.from({ length: 42 }, (_, i) => ({ type: "deployment_state", message: `dep-${i}` })),
          diagnostic: {
            evidence_by_tier: {
              primary: [{ message: "a" }, { message: "b" }, { message: "c" }],
              supporting: [{ message: "s1" }, { message: "s2" }],
              historical: [],
              debug: Array.from({ length: 37 }, () => ({ message: "old ready deployment" })),
            },
          },
        },
      },
    } as unknown as TrackedJobRecord;

    const summary = executionEvidenceSummary(job);
    expect(summary.hasTiers).toBe(true);
    expect(summary.primary).toBe(3);
    expect(summary.supporting).toBe(2);
    expect(summary.debug).toBe(37);
    expect(formatExecutionEvidenceLabel(job)).toBe("Primary: 3 · Supporting: 2");
    expect(formatExecutionDebugEvidenceLabel(job)).toBe("Debug records: 37");
  });

  it("falls back to flat count for non-tiered executions", () => {
    const job = {
      id: "job-dom",
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        readonly_execution: {
          evidence: [{ type: "domain_record", message: "invoicepilot.com" }],
        },
      },
    } as unknown as TrackedJobRecord;
    expect(formatExecutionEvidenceLabel(job)).toBe("Evidence: 1");
    expect(formatExecutionDebugEvidenceLabel(job)).toBe("");
  });
});
