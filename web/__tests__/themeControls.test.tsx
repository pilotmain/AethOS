import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("theme controls", () => {
  it("globals define accent gradient and glow tokens", () => {
    const path = join(__dirname, "../app/globals.css");
    const text = readFileSync(path, "utf8");
    expect(text).toContain("--aethos-accent-grad");
    expect(text).toContain("--aethos-accent-glow");
  });

  it("globals define the cyan→violet signature palette + glass tokens", () => {
    const text = readFileSync(join(__dirname, "../app/globals.css"), "utf8");
    // Violet secondary accent exists.
    expect(text).toContain("--aethos-violet");
    // The signature gradient runs cyan (#22d3ee) → violet (#a78bfa), not the old cyan→green.
    expect(text).toMatch(/--aethos-accent-grad:\s*linear-gradient\([^)]*#22d3ee[^)]*#a78bfa/);
    // Glassmorphic surface + accent glow tokens are present (drive the panel look).
    expect(text).toContain("--aethos-glass-bg");
    expect(text).toContain("--aethos-glass-border");
    expect(text).toContain("--aethos-glow-cyan");
    expect(text).toContain("--aethos-glow-violet");
  });

  it("applies the gradient signature to every MC panel/header title consistently", () => {
    const text = readFileSync(join(__dirname, "../app/globals.css"), "utf8");
    // A single scoped rule gradients all h1/h2 inside the MC shell — so every one
    // of the ~118 panel titles + the header are consistent without per-file edits.
    expect(text).toContain("[data-mc-scroll-root] h1");
    expect(text).toContain("[data-mc-scroll-root] h2");
    // Escape hatch + body accent utility exist.
    expect(text).toContain("aethos-no-gradient");
    expect(text).toContain("aethos-accent-text");
  });

  it("the shared card style is glassmorphic and exposes gradient-text + glow helpers", () => {
    const text = readFileSync(join(__dirname, "../lib/missionControl/layout.ts"), "utf8");
    // Panels render on a translucent glass surface with blur (not the old solid card).
    expect(text).toContain("backdropFilter");
    expect(text).toContain("glassBg");
    // Cyan→violet signature primitives are exported for logos/headings.
    expect(text).toContain("mcGradientTextStyle");
    expect(text).toContain("mcGlow");
    expect(text).toContain("violet");
  });
});
