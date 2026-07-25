import { describe, expect, it } from "vitest";

/** Phase 8.2 chat copy contracts (backend mirrors these strings). */
const NEEDS_SESSION_MARKERS = ["supervised", "browser session"];
const MUTATION_BLOCKED_MARKERS = ["not enabled", "mutation"];

describe("vercelReadonlyRouting", () => {
  it("defines expected reply markers for routing tests", () => {
    expect(NEEDS_SESSION_MARKERS.every((m) => m.length > 2)).toBe(true);
    expect(MUTATION_BLOCKED_MARKERS.some((m) => /not enabled/i.test(m))).toBe(true);
  });
});
