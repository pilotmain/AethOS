import { describe, expect, it } from "vitest";

import {
  executionDataSourceLabel,
  readonlyExecutionBadge,
} from "@/lib/missionControl/operationPreflight";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("apiBackedReadonlyExecutionArtifact", () => {
  it("shows provider API execution and readonly badge", () => {
    const job = {
      job_type: "readonly_execution_vercel",
      status: "completed",
      params: {
        read_only: true,
        auth_method_label: "Vercel API token",
        data_source: "provider_api",
        operation_type: "list_domains",
        readonly_execution: {
          provider: "vercel",
          operation_type: "list_domains",
          target_name: "invoicepilot",
          auth_method_label: "Vercel API token",
          data_source: "provider_api",
          read_only: true,
        },
      },
    } as unknown as TrackedJobRecord;
    expect(readonlyExecutionBadge(job)).toMatch(/No mutation performed/i);
    expect(executionDataSourceLabel(job)).toBe("Provider API execution");
    expect(job.params?.auth_method_label).toBe("Vercel API token");
  });
});
