import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { LEGACY_FORBIDDEN_PATHS } from "@/lib/api/routeProbe";

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

const ALLOW_LEGACY_PATH_REF = new Set([
  "lib/api/routeProbe.ts",
  "app/api/setup-creds/route.ts",
  "app/api/v1/auth/ping/route.ts",
  "app/api/v1/setup/auth-diagnostics/route.ts",
]);

describe("noLegacyEndpointProbes", () => {
  it("web source does not reference legacy auth/setup probe paths", () => {
    const root = join(process.cwd());
    const files = walk(root).filter((f) => {
      const rel = f.replace(`${root}/`, "");
      if (rel.includes("__tests__/")) return false;
      if (ALLOW_LEGACY_PATH_REF.has(rel)) return false;
      return !rel.includes("routeProbe.ts");
    });
    const combined = files.map((f) => readFileSync(f, "utf8")).join("\n");
    for (const path of LEGACY_FORBIDDEN_PATHS) {
      expect(combined).not.toContain(path);
    }
  });
});
