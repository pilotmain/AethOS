import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

import { LEGACY_FORBIDDEN_PATHS } from "@/lib/api/routeProbe";

function walk(dir: string, out: string[] = []): string[] {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (name === "node_modules" || name === ".next") continue;
    const stat = fs.statSync(full);
    if (stat.isDirectory()) walk(full, out);
    else if (/\.(ts|tsx)$/.test(name)) out.push(full);
  }
  return out;
}

// Files that legitimately contain the legacy path strings: the routeProbe
// allowlist source, the legacy-route shim definitions (which return 410/redirect),
// and test fixtures that assert about these paths. None of these are callers.
const ALLOW_LEGACY_PATH_REF = [
  "lib/api/routeProbe.ts",
  "app/api/setup-creds/route.ts",
  "app/api/v1/auth/ping/route.ts",
  "app/api/v1/setup/auth-diagnostics/route.ts",
];

describe("no legacy endpoint callers in web source", () => {
  it("does not reference forbidden legacy paths outside routeProbe", () => {
    const cwd = process.cwd();
    const root = cwd.endsWith(`${path.sep}web`) ? cwd : path.join(cwd, "web");
    const files = walk(root);
    const hits: string[] = [];
    for (const file of files) {
      const rel = file.replace(`${root}${path.sep}`, "");
      if (rel.includes("__tests__")) continue;
      if (ALLOW_LEGACY_PATH_REF.some((allowed) => rel.endsWith(allowed))) continue;
      if (rel.includes("routeProbe.ts")) continue;
      const text = fs.readFileSync(file, "utf8");
      for (const legacy of LEGACY_FORBIDDEN_PATHS) {
        if (text.includes(legacy)) hits.push(`${file}: ${legacy}`);
      }
    }
    expect(hits).toEqual([]);
  });
});
