import { describe, expect, it } from "vitest";

import { normalizeBrowserCapability } from "@/lib/settings/browserCapability";

describe("browserDiagnosticsDetails", () => {
  it("shows runtime python launch probe and cache path", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      execution_ready: false,
      playwright_package: "installed",
      chromium_browser: "missing",
      diagnostics: {
        python_executable: "/Users/raya/aethos/.venv/bin/python",
        python_version: "3.11.9",
        playwright_package: "installed",
        playwright_version: "1.49.0",
        chromium_browser: "missing",
        launch_probe_ok: false,
        launch_probe_error: "Executable doesn't exist",
        browser_cache_path: "/Users/raya/Library/Caches/ms-playwright",
        chromium_executable_path: "/path/chromium",
        recommended_install_command:
          "/Users/raya/aethos/.venv/bin/python -m playwright install chromium",
      },
    });
    expect(vm.runtimePython).toContain(".venv/bin/python");
    expect(vm.pythonVersion).toBe("3.11.9");
    expect(vm.launchProbeOk).toBe(false);
    expect(vm.launchProbeError).toContain("Executable");
    expect(vm.browserCachePath).toContain("ms-playwright");
    expect(vm.recommendedInstallCommand).toContain("playwright install chromium");
  });
});
