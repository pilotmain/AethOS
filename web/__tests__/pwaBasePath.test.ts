import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { authLoginPath, withBasePath } from "@/lib/pwa/basePath";

function webRoot(): string {
  const cwd = process.cwd();
  return cwd.endsWith("/web") ? cwd : join(cwd, "web");
}

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

const NEXT_NAV_WITH_BASE_PATH = /router\.(push|replace)\([^)]*withBasePath/;
const NEXT_LINK_WITH_BASE_PATH = /<Link[^>]*href=\{?\s*withBasePath/;
const NEXT_NAV_LITERAL_AETHOS = /router\.(push|replace)\(\s*["'`]\/aethos/;
const NEXT_LINK_LITERAL_AETHOS = /<Link[^>]*href=["'`]\/aethos/;

describe("withBasePath", () => {
  it("prefixes paths when NEXT_PUBLIC_BASE_PATH is set", () => {
    const prev = process.env.NEXT_PUBLIC_BASE_PATH;
    process.env.NEXT_PUBLIC_BASE_PATH = "/aethos";
    expect(withBasePath("/sw.js")).toBe("/aethos/sw.js");
    process.env.NEXT_PUBLIC_BASE_PATH = prev;
  });

  it("leaves paths unchanged without a base path", () => {
    const prev = process.env.NEXT_PUBLIC_BASE_PATH;
    process.env.NEXT_PUBLIC_BASE_PATH = "";
    expect(withBasePath("/sw.js")).toBe("/sw.js");
    process.env.NEXT_PUBLIC_BASE_PATH = prev;
  });

  it("auth login path stays under base path", () => {
    const prev = process.env.NEXT_PUBLIC_BASE_PATH;
    process.env.NEXT_PUBLIC_BASE_PATH = "/aethos";
    expect(authLoginPath()).toBe("/aethos/login");
    process.env.NEXT_PUBLIC_BASE_PATH = prev;
  });
});

describe("base path navigation guard", () => {
  const allow = new Set([
    "lib/pwa/basePath.ts",
    "lib/pwa/registerServiceWorker.ts",
    "lib/pwa/useWebPush.ts",
    "__tests__/pwaBasePath.test.ts",
  ]);

  it("never wraps Next router or Link navigation in withBasePath", () => {
    const root = webRoot();
    const hits: string[] = [];
    for (const file of walk(root)) {
      const rel = file.replace(`${root}/`, "");
      if (allow.has(rel)) continue;
      const text = readFileSync(file, "utf8");
      if (NEXT_NAV_WITH_BASE_PATH.test(text)) hits.push(`${rel}: router + withBasePath`);
      if (NEXT_LINK_WITH_BASE_PATH.test(text)) hits.push(`${rel}: Link + withBasePath`);
      if (NEXT_NAV_LITERAL_AETHOS.test(text)) hits.push(`${rel}: router literal /aethos`);
      if (NEXT_LINK_LITERAL_AETHOS.test(text)) hits.push(`${rel}: Link literal /aethos`);
    }
    expect(hits).toEqual([]);
  });

  it("login page redirects authenticated users with a bare app path", () => {
    const loginPage = readFileSync(join(webRoot(), "app/login/page.tsx"), "utf8");
    expect(loginPage).toMatch(/router\.replace\(\s*["'`]\/["'`]\s*\)/);
    expect(loginPage).not.toMatch(/withBasePath/);
  });

  it("verify-email success link uses bare href for Next Link", () => {
    const page = readFileSync(join(webRoot(), "app/verify-email/page.tsx"), "utf8");
    expect(page).toMatch(/<Link[^>]*href=["'`]\/\?verified=1["'`]/);
    expect(page).not.toMatch(/withBasePath/);
  });
});
