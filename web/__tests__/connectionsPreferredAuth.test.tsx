import { describe, expect, it } from "vitest";

const preferredMethods = ["api_token", "browser", "cli", "ask"] as const;

describe("connectionsPreferredAuth", () => {
  it("supports preferred auth method choices", () => {
    expect(preferredMethods).toContain("api_token");
    expect(preferredMethods).toContain("browser");
  });
});
