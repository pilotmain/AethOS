import { describe, expect, it } from "vitest";

import { normalizeBrowserCapability } from "@/lib/settings/browserCapability";

describe("browserDiagnosticsAlwaysVisible", () => {
  it("shows diagnostics when browser automation is enabled even if runtime failed", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      execution_ready: false,
      execution_label: "Launch probe failed",
      playwright_package: "installed",
      diagnostics: {
        playwright_package: "installed",
        launch_probe_ok: false,
        launch_probe_error: "mock failure",
        execution_ready: false,
      },
    });
    expect(vm.showDiagnostics).toBe(true);
    expect(vm.playwrightPackage).toBe("installed");
  });
});
