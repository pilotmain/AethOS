import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const src = readFileSync(
  fileURLToPath(new URL("../components/auth/TenantSetupWizard.tsx", import.meta.url)),
  "utf-8",
);

describe("TenantSetupWizard — no premature exit during onboarding", () => {
  it("does NOT auto-exit to Mission Control when onboarding becomes complete", () => {
    // Regression: on hosted, LLM reasoning is already on, so saving the FIRST provider
    // key flipped server `complete` and an effect called onDone() — kicking the user into
    // Mission Control before they could add a second provider for the arbiter.
    expect(src).not.toMatch(/state\?\.complete\s*\)\s*onDone\(\)/);
    expect(src).not.toMatch(/if\s*\(\s*state\?\.complete\s*\)\s*onDone/);
  });

  it("leaves the wizard only via an explicit finish action", () => {
    expect(src).toContain("Finish & open Mission Control");
    expect(src).toMatch(/const onFinish[\s\S]*?onDone\(\)/);
  });

  it("is its own scroll container so the Finish button is always reachable", () => {
    // The global app shell sets body { overflow: hidden } for Mission Control, which
    // clips this taller card. The wizard must scroll internally (regression: the page
    // could not scroll, hiding the Finish button).
    expect(src).toMatch(/overflowY:\s*["']auto["']/);
  });
});
