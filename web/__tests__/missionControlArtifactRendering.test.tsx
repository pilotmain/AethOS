import { describe, expect, it } from "vitest";

import {
  jobArtifactPreview,
  jobArtifactSummary,
  jobFullReport,
} from "@/lib/missionControl/jobArtifacts";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

describe("missionControlArtifactRendering", () => {
  const job: TrackedJobRecord = {
    id: "job-mc-1",
    title: "Competitors",
    job_type: "comparison_brief",
    status: "completed",
    provider_used: "anthropic",
    model_used: "claude-test",
    result_preview: "LangGraph leads agent runtimes",
    result_summary: "- LangGraph\n- CrewAI\n- Open Mission Control → Jobs for the full report",
    full_result: "# Competitors\n\n- LangGraph\n- CrewAI\n\n" + "detail ".repeat(200),
    params: { provider_fallback: false },
  };

  it("uses preview and summary separately from full report", () => {
    expect(jobArtifactPreview(job)).toMatch(/LangGraph/);
    expect(jobArtifactSummary(job)).toMatch(/Mission Control/);
    const full = jobFullReport(job);
    expect(full).toContain("# Competitors");
    expect(full.length).toBeGreaterThan(jobArtifactSummary(job).length);
  });

  it("prefers full_result over legacy result field", () => {
    const legacy: TrackedJobRecord = {
      ...job,
      full_result: undefined,
      result: "legacy body",
    };
    expect(jobFullReport(legacy)).toBe("legacy body");
  });
});
