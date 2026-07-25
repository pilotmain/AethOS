import { describe, expect, it } from "vitest";

import { recordPollOutcome } from "@/lib/chat/jobEventPolling";

describe("jobEventPollingBackoff", () => {
  it("stays silent for first two failures", () => {
    expect(recordPollOutcome(0, false)).toEqual({ consecutiveFailures: 1, showStatus: false });
    expect(recordPollOutcome(1, false)).toEqual({ consecutiveFailures: 2, showStatus: false });
  });

  it("shows status from third failure onward", () => {
    expect(recordPollOutcome(2, false)).toEqual({ consecutiveFailures: 3, showStatus: true });
    expect(recordPollOutcome(5, false)).toEqual({ consecutiveFailures: 6, showStatus: true });
  });

  it("clears status after success", () => {
    expect(recordPollOutcome(4, true)).toEqual({ consecutiveFailures: 0, showStatus: false });
  });
});
