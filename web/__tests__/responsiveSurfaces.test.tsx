import { describe, expect, it } from "vitest";

describe("responsive workspace surfaces", () => {
  it("setup wizard module is importable for mobile onboarding", async () => {
    const mod = await import("@/components/onboarding/SetupWizard");
    expect(mod.SetupWizard).toBeDefined();
  });
});
