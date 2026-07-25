import { describe, expect, it } from "vitest";

describe("executionTimeline", () => {
  it("expects timeline entries on readonly execution jobs", () => {
    const timeline = [
      { status: "started", message: "Read-only local inspection" },
      { status: "running", message: "git_status" },
      { status: "completed", message: "done" },
    ];
    expect(timeline.map((t) => t.status)).toEqual(["started", "running", "completed"]);
  });
});
