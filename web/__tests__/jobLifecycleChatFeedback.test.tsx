import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  mergeJobLifecycleEvents,
  readTrackedJobIds,
  registerProposedJobFromMeta,
  trackJobId,
} from "@/lib/chat/jobLifecycleBridge";
import type { CachedMessage } from "@/lib/chat/lanes";

describe("jobLifecycleChatFeedback", () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal("window", globalThis);
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
    });
  });

  it("tracks proposed job from meta", () => {
    registerProposedJobFromMeta({ proposed_job_id: "job-abc123" }, "");
    expect(readTrackedJobIds()).toContain("job-abc123");
  });

  it("tracks all stop preflight ids from meta and reply", () => {
    registerProposedJobFromMeta(
      { proposed_job_ids: "job-aaa,job-bbb,job-ccc" },
      "Prepared preflights `job-aaa` · `job-bbb` · `job-ccc`",
    );
    const ids = readTrackedJobIds();
    expect(ids).toContain("job-aaa");
    expect(ids).toContain("job-bbb");
    expect(ids).toContain("job-ccc");
  });

  it("appends job lifecycle bubbles without job_created spam", () => {
    const base: CachedMessage[] = [{ id: "1", role: "user", content: "hi" }];
    const events = [
      {
        id: "job-1:job_started",
        job_id: "job-1",
        event_type: "job_started" as const,
        message: "⏳ Job started — Draft MVP checklist",
        status: "running",
        job_type: "checklist_generation",
        session_id: "default",
        at: 1,
      },
      {
        id: "job-1:job_completed",
        job_id: "job-1",
        event_type: "job_completed" as const,
        message: "✅ Job completed — Draft MVP checklist",
        status: "completed",
        job_type: "checklist_generation",
        session_id: "default",
        at: 2,
      },
    ];
    const first = mergeJobLifecycleEvents(base, events, new Set());
    expect(first.messages).toHaveLength(3);
    expect(first.messages[1]?.role).toBe("system");
    const second = mergeJobLifecycleEvents(first.messages, events, first.seen);
    expect(second.messages).toHaveLength(3);
  });

  it("failed job shows failure bubble", () => {
    const { messages } = mergeJobLifecycleEvents(
      [],
      [
        {
          id: "job-2:job_failed",
          job_id: "job-2",
          event_type: "job_failed",
          message: "⚠️ Job failed — Test: boom",
          status: "failed",
          job_type: "manual_note",
          session_id: "default",
          at: 1,
        },
      ],
      new Set(),
    );
    expect(messages[0]?.content).toMatch(/⚠️/);
  });

  it("trackJobId dedupes", () => {
    trackJobId("job-x");
    trackJobId("job-x");
    expect(readTrackedJobIds().filter((id) => id === "job-x")).toHaveLength(1);
  });
});
