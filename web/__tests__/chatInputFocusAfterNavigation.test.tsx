import { describe, expect, it } from "vitest";

import { isChatHomeRoute } from "@/lib/chat/focus";

describe("chatInputFocusAfterNavigation", () => {
  it("refocuses when returning to Chat from Mission Control", () => {
    expect(isChatHomeRoute("/mission-control")).toBe(false);
    expect(isChatHomeRoute("/")).toBe(true);
  });

  it("treats missing pathname as Chat home", () => {
    expect(isChatHomeRoute(null)).toBe(true);
  });
});
