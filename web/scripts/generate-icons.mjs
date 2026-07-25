/**
 * Regenerate raster icons from public/icons/icon.svg.
 * Run: node scripts/generate-icons.mjs
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const iconsDir = join(root, "public", "icons");
const svg = readFileSync(join(iconsDir, "icon.svg"));

async function png(size, out, padding = 0) {
  const inner = size - padding * 2;
  const raster = await sharp(svg).resize(inner, inner).png().toBuffer();
  if (padding > 0) {
    await sharp(raster)
      .extend({
        top: padding,
        bottom: padding,
        left: padding,
        right: padding,
        background: { r: 10, g: 12, b: 16, alpha: 1 },
      })
      .png()
      .toFile(out);
  } else {
    await sharp(raster).toFile(out);
  }
}

await png(192, join(iconsDir, "icon-192.png"));
await png(512, join(iconsDir, "icon-512.png"));
await png(512, join(iconsDir, "icon-512-maskable.png"), 64);
await png(180, join(iconsDir, "apple-touch-icon.png"));
await sharp(svg).resize(32, 32).png().toFile(join(root, "public", "favicon.png"));
await sharp(join(root, "public", "favicon.png"))
  .resize(32, 32)
  .toFile(join(root, "public", "favicon.ico"));

console.log("Icons generated in public/icons and public/favicon.ico");
