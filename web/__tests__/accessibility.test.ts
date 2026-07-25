import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const root = path.resolve(__dirname, "..");
const css = readFileSync(path.join(root, "app", "globals.css"), "utf-8");
const layout = readFileSync(path.join(root, "app", "layout.tsx"), "utf-8");

describe("§11 accessibility contract", () => {
  it("defines a visible keyboard focus indicator (WCAG 2.4.7)", () => {
    expect(css).toMatch(/:focus-visible\s*\{/);
    expect(css).toMatch(/outline:\s*2px solid var\(--aethos-accent/);
  });

  it("provides a screen-reader-only utility", () => {
    expect(css).toMatch(/\.sr-only\s*\{/);
  });

  it("provides a skip-to-content link (WCAG 2.4.1)", () => {
    expect(css).toMatch(/\.aethos-skip-link\s*\{/);
    expect(layout).toContain('href="#main-content"');
    expect(layout).toContain('id="main-content"');
  });

  it("declares the document language", () => {
    expect(layout).toMatch(/<html lang="en">/);
  });

  it("honors reduced-motion preferences", () => {
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\)/);
  });
});
