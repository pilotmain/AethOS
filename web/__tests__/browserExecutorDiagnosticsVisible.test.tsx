import { describe, expect, it } from "vitest";

import { normalizeBrowserCapability } from "@/lib/settings/browserCapability";

describe("browserExecutorDiagnosticsVisible", () => {
  it("shows executor and profile store diagnostics when runtime blocked", () => {
    const vm = normalizeBrowserCapability({
      enabled: true,
      execution_ready: false,
      foundation_label: "Ready",
      execution_label: "Playwright runtime not ready",
      saved_profile_count: 2,
      profile_store: { profile_count: 2, profile_store_path: "/data/profiles" },
      executor_status: {
        running: true,
        thread_id: 12345,
        queue_depth: 0,
        active_operation: null,
        last_error: "boundary violation",
        last_success_at: null,
      },
      diagnostics: {
        playwright_package: "installed",
        chromium_browser: "installed",
        execution_ready: false,
      },
    });
    expect(vm.savedProfileCount).toBe(2);
    expect(vm.profileStorePath).toBe("/data/profiles");
    expect(vm.executorRunning).toBe(true);
    expect(vm.executorThreadId).toBe("12345");
    expect(vm.executorLastError).toBe("boundary violation");
    expect(vm.showDiagnostics).toBe(true);
  });
});
