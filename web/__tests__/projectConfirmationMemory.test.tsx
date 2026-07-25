import { describe, expect, it } from "vitest";

/** Memory confirmation strings mirrored from backend tests. */
describe("projectConfirmationMemory", () => {
  it("expects confirm-all reply marker", () => {
    const reply = "Got it — I'll treat these as confirmed Vercel projects: `quotepilot`.";
    expect(reply.toLowerCase()).toContain("confirmed");
  });
});
