import { describe, expect, it } from "vitest";

import { normalizeBrowserCapability } from "@/lib/settings/browserCapability";

describe("browserSessionStatusCard", () => {
  it("shows installed vs unavailable execution labels", () => {
    const missing = normalizeBrowserCapability({
      enabled: true,
      playwright_installed: false,
      execution_implemented: false,
      available: false,
      foundation_label: "Ready",
      execution_label: "Playwright package missing in AethOS runtime",
      playwright_package: "missing",
      chromium_browser: "missing",
      supports_login_sessions: "supervised_only",
    });
    expect(missing.executionLabel.toLowerCase()).toMatch(/playwright|chromium/);

    const ready = normalizeBrowserCapability({
      enabled: true,
      playwright_installed: true,
      execution_implemented: true,
      available: true,
      provider: "playwright",
      foundation_label: "Ready",
      execution_label: "Supervised sessions available",
      supports_login_sessions: "supervised_only",
    });
    expect(ready.executionLabel.toLowerCase()).toMatch(/supervised/);
    expect(ready.userMessage.toLowerCase()).not.toContain("fake");
  });
});
