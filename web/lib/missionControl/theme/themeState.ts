/** Theme state persistence — dark / light / system + accessibility modes. */

import type { McAccessibilityMode, McThemePreference } from "@/lib/missionControl/theme/operationalPalette";

const THEME_KEY = "aethos.mc.theme";
const A11Y_KEY = "aethos.mc.accessibility";

export function loadThemePreference(): McThemePreference {
  if (typeof window === "undefined") return "dark";
  const raw = window.localStorage.getItem(THEME_KEY);
  if (raw === "light" || raw === "dark" || raw === "system") return raw;
  return "dark";
}

export function saveThemePreference(theme: McThemePreference): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(THEME_KEY, theme);
}

export function loadAccessibilityMode(): McAccessibilityMode {
  if (typeof window === "undefined") return "standard";
  const raw = window.localStorage.getItem(A11Y_KEY);
  if (
    raw === "standard" ||
    raw === "high-readability" ||
    raw === "reduced-atmosphere" ||
    raw === "focus"
  ) {
    return raw;
  }
  return "standard";
}

export function saveAccessibilityMode(mode: McAccessibilityMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(A11Y_KEY, mode);
}

export function resolveSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
