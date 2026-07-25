import { describe, expect, it } from "vitest";

import { shouldAutoFocusChatInput } from "@/lib/chat/focus";

describe("chatInputFocusAfterSend", () => {
  it("allows refocus after send when nothing else is focused", () => {
    expect(shouldAutoFocusChatInput(null)).toBe(true);
  });

  it("blocks refocus when modal is open", () => {
    expect(shouldAutoFocusChatInput(null, { hasOpenDialog: true })).toBe(false);
  });
});
