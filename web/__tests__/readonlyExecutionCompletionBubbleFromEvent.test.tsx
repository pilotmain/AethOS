import { beforeEach, describe, expect, it, vi } from "vitest";

import { trackJobId, readTrackedJobIds } from "@/lib/chat/jobLifecycleBridge";

describe("readonlyExecutionCompletionBubbleFromEvent", () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
    });
    vi.stubGlobal("window", { sessionStorage: sessionStorage as Storage });
  });

  it("tracks execution job id so chat poll can receive job_completed", () => {
    trackJobId("job-exec-abc");
    expect(readTrackedJobIds()).toContain("job-exec-abc");
  });
});
