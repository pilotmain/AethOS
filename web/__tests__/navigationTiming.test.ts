import { describe, expect, it, vi } from "vitest";

import { isVerboseTraceEnabled, markNavigation } from "@/lib/perf/navigationTiming";

describe("navigationTiming", () => {
  it("is quiet unless verbose trace is enabled", () => {
    const store: Record<string, string> = {};
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
    });
    expect(isVerboseTraceEnabled()).toBe(false);
    const info = vi.spyOn(console, "info").mockImplementation(() => {});
    markNavigation("test");
    expect(info).not.toHaveBeenCalled();
    info.mockRestore();
    vi.unstubAllGlobals();
  });
});
