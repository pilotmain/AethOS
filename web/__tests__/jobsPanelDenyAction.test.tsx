import { describe, expect, it } from "vitest";

import { actionControlHint, normalizeActionsGrouped } from "@/lib/missionControl/actions";

describe("jobsPanelDenyAction", () => {
  it("pending action is waiting for approval", () => {
    expect(actionControlHint("pending")).toBe("Waiting for approval");
  });

  it("denied action has no pending controls in grouped data", () => {
    const grouped = normalizeActionsGrouped({
      pending: [
        {
          id: "act-p",
          action_type: "vercel_cli_probe",
          status: "pending",
          summary: "CLI probe",
        },
      ],
      approved: [],
      completed: [],
      failed: [],
      denied: [
        {
          id: "act-d",
          action_type: "vercel_cli_probe",
          status: "denied",
          summary: "CLI probe",
        },
      ],
    });
    expect(grouped.pending).toHaveLength(1);
    expect(grouped.denied).toHaveLength(1);
    expect(grouped.completed).toHaveLength(0);
  });

  it("completed action hint shows no approval state", () => {
    expect(actionControlHint("completed")).toBe("Completed");
    expect(actionControlHint("denied")).toBe("Denied by operator");
  });
});
