import { describe, expect, it } from "vitest";

describe("login first paint", () => {
  it("login route module loads without throwing", async () => {
    const mod = await import("../app/login/page");
    expect(mod.default).toBeDefined();
  });
});
