import { describe, expect, it } from "vitest";

import { normalizeJobsGrouped } from "@/lib/missionControl/trackedJobs";

describe("providerJobResultRendering", () => {
  it("shows anthropic provider and result preview for successful provider job", () => {
    const grouped = normalizeJobsGrouped({
      queued: [],
      running: [],
      completed: [
        {
          id: "job-ok",
          title: "research the top competitors to AethOS",
          job_type: "comparison_brief",
          status: "completed",
          provider_used: "anthropic",
          model_used: "claude-sonnet-4-20250514",
          result_preview: "## Competitors — LangGraph leads agent runtimes",
          result: "## Competitors\n\n- LangGraph\n- CrewAI",
          params: { provider_fallback: false },
        },
      ],
      failed: [],
      cancelled: [],
    });
    const row = grouped.completed[0];
    expect(row?.provider_used).toBe("anthropic");
    expect(row?.model_used).toContain("claude");
    expect(row?.result_preview).toMatch(/Competitors/);
    expect(row?.params?.provider_fallback).toBe(false);
  });

  it("marks fallback template jobs in params", () => {
    const grouped = normalizeJobsGrouped({
      queued: [],
      running: [],
      completed: [
        {
          id: "job-fb",
          title: "Roadmap",
          job_type: "roadmap_generation",
          status: "completed",
          provider_used: "none",
          model_used: "template",
          result_preview: "⚠️ Provider unavailable",
          params: { provider_fallback: true },
        },
      ],
      failed: [],
      cancelled: [],
    });
    expect(grouped.completed[0]?.params?.provider_fallback).toBe(true);
  });
});
