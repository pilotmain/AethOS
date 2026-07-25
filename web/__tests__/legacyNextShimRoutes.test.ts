import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("legacyNextShimRoutes", () => {
  const webRoot = process.cwd().endsWith("/web") ? process.cwd() : join(process.cwd(), "web");

  it("shim routes return deprecated JSON shape", () => {
    const setup = readFileSync(join(webRoot, "app/api/setup-creds/route.ts"), "utf8");
    const ping = readFileSync(join(webRoot, "app/api/v1/auth/ping/route.ts"), "utf8");
    const diag = readFileSync(join(webRoot, "app/api/v1/setup/auth-diagnostics/route.ts"), "utf8");
    expect(setup).toMatch(/deprecated:\s*true/);
    expect(setup).toMatch(/api_base/);
    expect(ping).toMatch(/deprecated:\s*true/);
    expect(diag).toMatch(/deprecated:\s*true/);
  });
});
