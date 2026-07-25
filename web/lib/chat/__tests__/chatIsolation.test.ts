import { describe, expect, it } from "vitest";

import { formatChatError, isPanelDegradedCopy, shouldUseDeterministicLane } from "@/lib/chat/lanes";
import { canSendChat, deriveChatHealth } from "@/lib/connection/chatHealth";

describe("deterministicChatIgnoresPanelDegraded", () => {
  it("classifies vercel login as deterministic", () => {
    expect(
      shouldUseDeterministicLane(
        "please login to vercel.com and give me a report of all the services health?",
      ),
    ).toBe(true);
  });

  it("never surfaces panel degraded as chat error text", () => {
    expect(formatChatError("Panel degraded — chat and other areas may still work.")).not.toMatch(
      /panel degraded/i,
    );
  });

  it("detects panel copy", () => {
    expect(isPanelDegradedCopy("Panel degraded — chat and other areas may still work.")).toBe(true);
  });
});

describe("chatHealthSeparateFromPanelHealth", () => {
  it("allows send when panel degraded but chat ready", () => {
    const h = deriveChatHealth({
      chat_ready: true,
      label: "Connected · Some panels delayed",
      panel: "degraded",
    });
    expect(canSendChat(h)).toBe(true);
  });
});
