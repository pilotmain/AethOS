import { describe, expect, it } from "vitest";

import {
  formatPackageLabel,
  normalizeBrowserCapability,
} from "@/lib/settings/browserCapability";

describe("browserRuntimeDiagnosticsCard", () => {
  it("shows runtime python and distinct package vs chromium", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      foundation_label: "Ready",
      execution_label: "Playwright package missing in AethOS runtime",
      playwright_package: "missing",
      chromium_browser: "missing",
      execution_ready: false,
      diagnostics: {
        python_executable: "/Users/raya/aethos/.venv/bin/python",
        playwright_package: "missing",
        chromium_browser: "missing",
        recommended_install_commands: [
          "/Users/raya/aethos/.venv/bin/python -m pip install playwright",
          "/Users/raya/aethos/.venv/bin/python -m playwright install chromium",
        ],
      },
    });
    expect(vm.runtimePython).toContain(".venv/bin/python");
    expect(formatPackageLabel(vm.playwrightPackage)).toBe("Missing");
    expect(formatPackageLabel(vm.chromiumBrowser)).toBe("Missing");
    expect(vm.installCommands.length).toBe(2);
    expect(vm.installCommands[0]).toContain("pip install playwright");
    expect(vm.userMessage.toLowerCase()).toContain("runtime");
  });

  it("handles missing diagnostics without crash", () => {
    const vm = normalizeBrowserCapability({ enabled: true });
    expect(vm.runtimePython).toBe("unknown");
    expect(vm.installCommands.length).toBeGreaterThan(0);
  });

  it("shows installed when execution ready", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      playwright_package: "installed",
      chromium_browser: "installed",
      execution_ready: true,
      diagnostics: {
        python_executable: "/venv/bin/python",
        playwright_package: "installed",
        chromium_browser: "installed",
        execution_ready: true,
      },
    });
    expect(formatPackageLabel(vm.playwrightPackage)).toBe("Installed");
    expect(vm.executionReady).toBe(true);
    expect(vm.userMessage.toLowerCase()).not.toContain("bare pip");
  });
});
