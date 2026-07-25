/** Theme-aware atmospheric cognition — ambient intensity adapts per theme & a11y. */

import type { AmbientMood } from "@/lib/missionControl/ambientPresence";
import type { McAccessibilityMode, McResolvedTheme } from "@/lib/missionControl/theme/operationalPalette";

type AmbientSlice = {
  tint: string;
  glow: string;
  sidebar: string;
  focus: string;
  background: string;
};

const DARK_AMBIENT: Record<AmbientMood, AmbientSlice> = {
  stable: {
    tint: "rgba(148,163,184,0.008)",
    glow: "none",
    sidebar: "rgba(14,14,22,0.96)",
    focus: "rgba(34,211,238,0.10)",
    background: "linear-gradient(160deg, #07070c 0%, #0c0c14 55%, #07070c 100%)",
  },
  informational: {
    tint: "rgba(59,130,246,0.01)",
    glow: "none",
    sidebar: "rgba(14,16,24,0.96)",
    focus: "rgba(96,165,250,0.12)",
    background: "linear-gradient(160deg, #07070c 0%, #0e1018 55%, #07070c 100%)",
  },
  elevated: {
    tint: "rgba(251,191,36,0.012)",
    glow: "none",
    sidebar: "rgba(18,16,14,0.96)",
    focus: "rgba(251,191,36,0.14)",
    background: "linear-gradient(160deg, #07070c 0%, #12100c 55%, #07070c 100%)",
  },
  critical: {
    tint: "rgba(248,113,113,0.014)",
    glow: "none",
    sidebar: "rgba(22,14,14,0.96)",
    focus: "rgba(248,113,113,0.16)",
    background: "linear-gradient(160deg, #07070c 0%, #140e0e 55%, #07070c 100%)",
  },
};

const LIGHT_AMBIENT: Record<AmbientMood, AmbientSlice> = {
  stable: {
    tint: "rgba(59,130,246,0.015)",
    glow: "none",
    sidebar: "rgba(255,255,255,0.99)",
    focus: "rgba(8,145,178,0.10)",
    background: "linear-gradient(160deg, #f2f3f5 0%, #eef0f4 50%, #f2f3f5 100%)",
  },
  informational: {
    tint: "rgba(59,130,246,0.02)",
    glow: "none",
    sidebar: "rgba(255,255,255,0.99)",
    focus: "rgba(37,99,235,0.10)",
    background: "linear-gradient(160deg, #f2f3f5 0%, #eceff5 50%, #f2f3f5 100%)",
  },
  elevated: {
    tint: "rgba(217,119,6,0.02)",
    glow: "none",
    sidebar: "rgba(255,255,255,0.99)",
    focus: "rgba(217,119,6,0.11)",
    background: "linear-gradient(160deg, #f2f3f5 0%, #f3f0ea 50%, #f2f3f5 100%)",
  },
  critical: {
    tint: "rgba(220,38,38,0.02)",
    glow: "none",
    sidebar: "rgba(255,255,255,0.99)",
    focus: "rgba(220,38,38,0.11)",
    background: "linear-gradient(160deg, #f2f3f5 0%, #f5ecec 50%, #f2f3f5 100%)",
  },
};

export function getThemeAmbientPalette(
  mood: AmbientMood,
  theme: McResolvedTheme,
  accessibility: McAccessibilityMode,
): AmbientSlice {
  const base = theme === "light" ? LIGHT_AMBIENT[mood] : DARK_AMBIENT[mood];
  if (accessibility === "reduced-atmosphere" || accessibility === "focus") {
    return {
      ...base,
      tint: "transparent",
      glow: "none",
      background: theme === "light" ? "#f2f3f5" : "#07070c",
      sidebar: theme === "light" ? "rgba(255,255,255,0.99)" : "rgba(16,20,32,0.98)",
    };
  }
  return base;
}
