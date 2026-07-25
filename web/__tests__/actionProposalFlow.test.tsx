import { describe, expect, it } from "vitest";

import { emptyActionsGrouped, normalizeActionsGrouped } from "@/lib/missionControl/actions";

describe("actionProposalFlow", () => {
  it("normalizes grouped actions", () => {
    const g = normalizeActionsGrouped({
      pending: [{ id: "act-1", action_type: "runtime_restart", status: "pending", summary: "x" }],
      completed: [],
    });
    expect(g.pending).toHaveLength(1);
    expect(g.pending[0]?.id).toBe("act-1");
  });

  it("handles malformed grouped payload", () => {
    expect(normalizeActionsGrouped(undefined).pending).toEqual([]);
    expect(emptyActionsGrouped().failed).toEqual([]);
  });
});
