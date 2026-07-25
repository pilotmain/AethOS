import { describe, expect, it } from "vitest";

import { mergeJobLifecycleEvents } from "@/lib/chat/jobLifecycleBridge";
import { normalizeJobsGrouped } from "@/lib/missionControl/trackedJobs";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("providerJobFailureRendering", () => {
  it("shows failed provider jobs in grouped panel", () => {
    const grouped = normalizeJobsGrouped({
      queued: [],
      running: [],
      completed: [],
      failed: [
        {
          id: "job-fail",
          title: "Research",
          job_type: "research_plan",
          status: "failed",
          failure_reason: "Invalid Anthropic API key.",
        },
      ],
      cancelled: [],
    });
    expect(grouped.failed[0]?.failure_reason).toMatch(/Invalid Anthropic/i);
  });

  it("renders provider failure lifecycle bubble once", () => {
    const first = mergeJobLifecycleEvents(
      [],
      [
        {
          id: "job-f:job_failed",
          job_id: "job-f",
          event_type: "job_failed",
          message: "⚠️ Job failed — Research: Invalid Anthropic API key.",
          status: "failed",
          job_type: "research_plan",
          session_id: "default",
          at: 1,
        },
      ],
      new Set(),
    );
    expect(first.messages[0]?.content).toMatch(/Invalid Anthropic/i);
    const second = mergeJobLifecycleEvents(
      first.messages,
      [
        {
          id: "job-f:job_failed",
          job_id: "job-f",
          event_type: "job_failed",
          message: "⚠️ Job failed — Research: Invalid Anthropic API key.",
          status: "failed",
          job_type: "research_plan",
          session_id: "default",
          at: 1,
        },
      ],
      first.seen,
    );
    expect(second.messages).toHaveLength(1);
  });
});
