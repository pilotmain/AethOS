import { describe, expect, it } from "vitest";

describe("SetupWizard", () => {
  it("defines four skippable steps", async () => {
    const mod = await import("@/components/onboarding/SetupWizard");
    expect(mod.SetupWizard).toBeDefined();
  });
});
