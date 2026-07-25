import { describe, expect, it } from "vitest";

import { formatChatError } from "@/lib/chat/lanes";

describe("structuredInventoryFailure", () => {
  it("maps fetch failures to structured connection message", () => {
    expect(formatChatError("Failed to fetch")).toMatch(/connection dropped/i);
  });

  it("passes through normal backend error messages", () => {
    expect(formatChatError("Job failed — browser runtime unavailable")).toMatch(/browser runtime unavailable/i);
  });
});
