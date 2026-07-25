import { describe, expect, it } from "vitest";

import { normalizeActionsGrouped } from "@/lib/missionControl/actions";
import { mcFailureAffectsChat } from "@/lib/missionControl/panelError";

describe("jobsActionsPanel", () => {
  it("separates pending and completed actions", () => {
    const grouped = normalizeActionsGrouped({
      pending: [
        {
          id: "act-a",
          action_type: "vercel_cli_probe",
          status: "pending",
          summary: "CLI probe",
        },
      ],
      approved: [],
      completed: [
        {
          id: "act-b",
          action_type: "runtime_restart",
          status: "completed",
          summary: "Restart",
          result: "done",
        },
      ],
      failed: [],
      denied: [],
    });
    expect(grouped.pending).toHaveLength(1);
    expect(grouped.completed).toHaveLength(1);
  });

  it("jobs action failure does not affect chat", () => {
    expect(mcFailureAffectsChat("Actions request failed: 500")).toBe(false);
  });
});
