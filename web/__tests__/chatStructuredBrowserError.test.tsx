import { describe, expect, it } from "vitest";

import { formatChatError } from "@/lib/chat/lanes";

describe("chatStructuredBrowserError", () => {
  it("replaces raw Failed to fetch with structured copy", () => {
    expect(formatChatError("Failed to fetch")).toMatch(/API connection dropped/i);
  });
});
