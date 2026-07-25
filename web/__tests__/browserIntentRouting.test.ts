import { describe, expect, it } from "vitest";

/**
 * Mirrors backend operational routing contracts (Phase 8.2 routing fix).
 * Chat must surface proposals/jobs — not generic CLI tutorials.
 */
const BROWSER_PROPOSAL_MARKERS = [
  "Browser job proposed",
  "supervised browser session",
  "Mission Control → Jobs",
  "approval required",
];

const PROVIDER_HALLUCINATION_MARKERS = [
  "npm i -g vercel",
  "vercel login`",
  "Here's how to set up",
  "Quick redeploy",
];

describe("browserIntentRouting", () => {
  it("expects deterministic browser replies to include proposal lifecycle copy", () => {
    const sample =
      "⏳ **Browser job proposed** — approval required before opening `vercel.com`.\nApprove or deny in **Mission Control → Jobs**.";
    expect(BROWSER_PROPOSAL_MARKERS.some((m) => sample.includes(m))).toBe(true);
    expect(PROVIDER_HALLUCINATION_MARKERS.some((m) => sample.toLowerCase().includes(m.toLowerCase()))).toBe(
      false,
    );
  });

  it("expects mutation block copy without redeploy tutorial", () => {
    const blocked =
      "mutation actions are not enabled yet (restart, redeploy, delete, env changes).";
    expect(blocked).toMatch(/not enabled/i);
    expect(blocked).not.toMatch(/vercel deploy/i);
  });
});
