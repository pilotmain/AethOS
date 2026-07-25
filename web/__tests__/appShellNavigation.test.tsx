import { describe, expect, it } from "vitest";

describe("app shell navigation", () => {
  it("exposes primary surfaces in AppNav", async () => {
    const mod = await import("../components/AppNav");
    expect(mod.AppNav).toBeDefined();
    expect(mod.prefetchMissionControlChunk).toBeDefined();
  });
});
