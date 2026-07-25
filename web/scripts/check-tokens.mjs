#!/usr/bin/env node
// Token guard (UI/UX handoff §1/§End): components must use the --aethos-* token
// system (directly or via mcColors), never raw hardcoded hex. This keeps one
// palette as the single source of truth so changing a token restyles every page.
//
// Allowed: var(--aethos-*), mcColors.*, rgb()/rgba(), color-mix(), and literal
// rgb() brand colors that have no token equivalent. Forbidden: #rrggbb / #rrggbbaa.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = new URL("../components/", import.meta.url).pathname;
const HEX = /#[0-9a-fA-F]{6}\b/;

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (/\.(tsx?|css)$/.test(p)) out.push(p);
  }
  return out;
}

const offenders = [];
for (const file of walk(ROOT)) {
  const lines = readFileSync(file, "utf8").split("\n");
  lines.forEach((line, i) => {
    if (HEX.test(line)) offenders.push(`${file.replace(ROOT, "components/")}:${i + 1}: ${line.trim()}`);
  });
}

if (offenders.length) {
  console.error(`✗ Raw hex colors found in components (use --aethos-* tokens):\n`);
  for (const o of offenders) console.error(`  ${o}`);
  console.error(`\n${offenders.length} offender(s). Replace with var(--aethos-*) or mcColors.*`);
  process.exit(1);
}
console.log("✓ No raw hex in components — single token palette intact.");
