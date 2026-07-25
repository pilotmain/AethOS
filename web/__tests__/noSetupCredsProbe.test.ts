import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { LEGACY_FORBIDDEN_PATHS, isLegacyForbiddenUrl } from "@/lib/api/routeProbe";

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      if (name === "node_modules" || name === ".next") continue;
      out.push(...walk(p));
    } else if (/\.(ts|tsx)$/.test(name)) {
      out.push(p);
    }
  }
  return out;
}

describe("noSetupCredsProbe", () => {
  it("web source does not call legacy setup-creds except shims and routeProbe guard", () => {
    const cwd = process.cwd();
    const root = cwd.endsWith(`${join("", "web")}`) || cwd.endsWith("/web") ? cwd : join(cwd, "web");
    const allow = new Set([
      "lib/api/routeProbe.ts",
      "app/api/setup-creds/route.ts",
      "app/api/v1/auth/ping/route.ts",
      "app/api/v1/setup/auth-diagnostics/route.ts",
      "__tests__/noSetupCredsProbe.test.ts",
      "__tests__/noLegacyEndpointCallsOnLoad.test.ts",
      "__tests__/noLegacyEndpointProbes.test.ts",
      "__tests__/legacyNextShimRoutes.test.ts",
    ]);
    const hits: string[] = [];
    for (const file of walk(root)) {
      const rel = file.replace(`${root}/`, "");
      if (allow.has(rel)) continue;
      if (rel.includes("__tests__/noLegacy") || rel.includes("__tests__/noSetup")) continue;
      const text = readFileSync(file, "utf8");
      for (const legacy of LEGACY_FORBIDDEN_PATHS) {
        if (text.includes(legacy)) hits.push(`${rel}: ${legacy}`);
      }
    }
    expect(hits).toEqual([]);
  });

  it("blocks legacy URLs in routeProbe guard", () => {
    expect(isLegacyForbiddenUrl("/api/setup-creds")).toBe(true);
    expect(isLegacyForbiddenUrl("http://127.0.0.1:8010/api/v1/health")).toBe(false);
  });

  it("Next setup-creds shim module exists", () => {
    const shim = join(
      process.cwd().endsWith("/web") ? process.cwd() : join(process.cwd(), "web"),
      "app/api/setup-creds/route.ts",
    );
    const text = readFileSync(shim, "utf8");
    expect(text).toContain("deprecated");
    expect(text).toContain("api_base");
  });
});
