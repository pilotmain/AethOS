import { describe, expect, it } from "vitest";

import { jobFullReport } from "@/lib/missionControl/jobArtifacts";
import {
  externalJobMode,
  externalJobTarget,
  usesExternalJobType,
} from "@/lib/missionControl/trackedJobs";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("externalHealthArtifactRendering", () => {
  const job: TrackedJobRecord = {
    id: "job-ext-mc",
    title: "Vercel service health check",
    job_type: "external_health_report",
    status: "completed",
    provider_used: "none",
    model_used: "external_health_report",
    result_preview: "none: All Systems Operational",
    result_summary: "- Public status source checked\n- Open Mission Control → Jobs for the full report",
    full_result:
      "# Vercel external health report\n\n## Sources\n\n- Public status\n\n" +
      Array.from({ length: 30 }, (_, i) => `Line ${i}: operational detail\n`).join(""),
    params: {
      target: "vercel",
      mode: "public",
      external_mode: "public",
      tool_used: "external_health_report",
      sources: [{ type: "public_status", label: "Vercel Status", available: true }],
    },
  };

  it("identifies external health jobs and metadata", () => {
    expect(usesExternalJobType(job.job_type)).toBe(true);
    expect(externalJobTarget(job)).toBe("vercel");
    expect(externalJobMode(job)).toBe("public");
    expect(job.params?.tool_used).toBe("external_health_report");
  });

  it("keeps full report separate from summary for Mission Control", () => {
    const full = jobFullReport(job);
    expect(full).toContain("# Vercel external health report");
    expect((job.result_summary || "").length).toBeLessThan(full.length);
  });
});
