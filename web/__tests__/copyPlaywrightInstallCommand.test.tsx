import { describe, expect, it } from "vitest";

import { primaryPlaywrightInstallCommand, normalizeBrowserCapability } from "@/lib/settings/browserCapability";

describe("copyPlaywrightInstallCommand", () => {
  it("uses recommended_install_command from diagnostics", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      execution_ready: false,
      diagnostics: {
        python_executable: "/venv/bin/python3",
        recommended_install_command: "/venv/bin/python3 -m playwright install chromium",
        recommended_install_commands: [
          "/venv/bin/python3 -m pip install playwright",
          "/venv/bin/python3 -m playwright install chromium",
        ],
      },
    });
    expect(primaryPlaywrightInstallCommand(vm)).toBe(
      "/venv/bin/python3 -m playwright install chromium",
    );
    expect(vm.recommendedInstallCommand).toContain("python3");
  });
});
