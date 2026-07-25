import { describe, expect, it } from "vitest";

import {
  browserCardHeadline,
  normalizeBrowserCapability,
} from "@/lib/settings/browserCapability";

describe("browserCapabilityCard", () => {
  it("normalizes off state for settings card", () => {
    const vm = normalizeBrowserCapability({
      enabled: false,
      available: false,
      provider: "none",
      requires_approval: true,
      supports_login_sessions: "supervised_only",
      status_label: "Off",
      foundation_label: "Off",
      execution_label: "Not available (foundation off)",
      env_var: "BROWSER_AUTOMATION_ENABLED",
      execution_implemented: false,
      active_session_count: 0,
      diagnostics: {
        python_executable: "/project/.venv/bin/python",
        playwright_package: "missing",
        chromium_browser: "missing",
      },
    });
    expect(browserCardHeadline(vm)).toBe("Browser automation");
    expect(vm.foundationLabel).toBe("Off");
    expect(vm.loginSessionsLabel).toBe("Supervised only");
    expect(vm.activeSessionCount).toBe(0);
  });

  it("enabled with execution shows supervised only", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      available: true,
      provider: "playwright",
      requires_approval: true,
      supports_login_sessions: "supervised_only",
      foundation_label: "Ready",
      execution_label: "Supervised sessions available",
      execution_implemented: true,
      execution_ready: true,
      playwright_package: "installed",
      chromium_browser: "installed",
      active_session_count: 1,
    });
    expect(vm.executionLabel).toMatch(/supervised/i);
    expect(vm.loginSessionsLabel).toBe("Supervised only");
    expect(vm.activeSessionCount).toBe(1);
    expect(vm.userMessage.toLowerCase()).toMatch(/manual|credentials/);
  });
});
