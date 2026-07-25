import { describe, expect, it } from "vitest";

function maskToken(token: string): string {
  if (token.length <= 8) return "*".repeat(token.length);
  return `${token.slice(0, 4)}${"*".repeat(Math.max(4, token.length - 8))}${token.slice(-4)}`;
}

describe("connectionsNoSecretLeakage", () => {
  it("masks token values for display", () => {
    const token = "vercel_test_token_abcdefghijklmnopqrstuvwxyz";
    const masked = maskToken(token);
    expect(masked).not.toContain("abcdefghijklmnopqrstuvwxyz");
  });
});
