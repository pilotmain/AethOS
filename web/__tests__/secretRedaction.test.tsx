import { describe, expect, it } from "vitest";

function maskSecret(value: string): string {
  const raw = value.trim();
  if (raw.length <= 8) return "*".repeat(raw.length);
  return `${raw.slice(0, 4)}${"*".repeat(Math.max(4, raw.length - 8))}${raw.slice(-4)}`;
}

describe("secretRedaction", () => {
  it("masks token middle segments", () => {
    const masked = maskSecret("vercel_test_token_abcdefghijklmnopqrstuvwxyz");
    expect(masked).not.toContain("abcdefghijklmnopqrstuvwxyz");
  });
});
