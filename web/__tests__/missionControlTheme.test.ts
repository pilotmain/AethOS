import { describe, expect, it } from "vitest";

import { resolveOperationalPalette } from "@/lib/missionControl/theme/operationalPalette";
import { saveThemePreference, loadThemePreference } from "@/lib/missionControl/theme/themeState";

describe("missionControlTheme", () => {
  it("dark high-readability increases nav contrast", () => {
    const standard = resolveOperationalPalette("dark", "standard");
    const high = resolveOperationalPalette("dark", "high-readability");
    expect(high.textNavInactive > standard.textNavInactive).toBe(true);
  });

  it("light theme uses calm operational palette", () => {
    const light = resolveOperationalPalette("light", "standard");
    expect(light.bg).toMatch(/^#/);
    expect(light.text).toBe("#0f0f12");
  });

  it("light theme uses crisp operational grounding surfaces", () => {
    const light = resolveOperationalPalette("light", "standard");
    expect(light.bgSurfacePrimary).toBe("#ffffff");
    expect(light.textStrong).toBe("#09090b");
    expect(light.textMuted).toBe("#3f3f46");
  });

  it("dark theme uses solid surface tokens", () => {
    const dark = resolveOperationalPalette("dark", "standard");
    expect(dark.bgCard).toMatch(/^#/);
    expect(dark.bgSurfacePrimary).toMatch(/^#/);
  });

  it("persists theme preference when localStorage available", () => {
    if (typeof window === "undefined") return;
    saveThemePreference("light");
    expect(loadThemePreference()).toBe("light");
    saveThemePreference("system");
    expect(loadThemePreference()).toBe("system");
  });
});
