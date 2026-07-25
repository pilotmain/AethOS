import { describe, expect, it } from "vitest";

import {
  operationPreflightFromJob,
  preflightExecutionStatusLines,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("phase93bExecutionCopy", () => {
  const job: TrackedJobRecord = {
    id: "job-pf93",
    title: "Vercel down diagnostic preflight",
    job_type: "vercel_down_diagnostic_preflight",
    status: "completed",
    params: {
      preflight_status: "ready_for_readonly_diagnostic",
      operation_preflight: {
        target_name: "talking-avatar-agent",
        target_status: "resolved",
        provider: "vercel",
        operation_type: "why_down",
        phase: "9.3B",
        read_only_execution_enabled: true,
        mutation_execution_enabled: false,
        approval_required: true,
        proposed_steps: ["Inspect latest deployment failures via Vercel API."],
      },
    },
  };

  it("shows phase 9.3B read-only execution availability", () => {
    const pf = operationPreflightFromJob(job);
    expect(pf?.phase).toBe("9.3B");
    expect(pf?.read_only_execution_enabled).toBe(true);
    const lines = preflightExecutionStatusLines(job);
    expect(lines.join(" ")).toMatch(/Phase 9\.3B/);
    expect(lines.join(" ")).toMatch(/Read-only execution · available after approval/);
    expect(lines.join(" ")).not.toMatch(/Phase 9\.2/);
  });
});
