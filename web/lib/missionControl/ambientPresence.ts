/** Phase 10.1.5.2 — Ambient operational presence — subtle environmental state. */

import type { CSSProperties } from "react";

import type { AttentionLevel } from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import { getThemeAmbientPalette } from "@/lib/missionControl/theme/atmosphericTheming";
import type { McAccessibilityMode, McResolvedTheme } from "@/lib/missionControl/theme/operationalPalette";

export type AmbientMood = "stable" | "informational" | "elevated" | "critical";

export type AmbientPresenceState = {
  mood: AmbientMood;
  attentionLevel: AttentionLevel;
  presenceLabel: string;
  rhythm: "calm" | "focused" | "alert";
  cssVars: Record<string, string>;
  shellStyle: CSSProperties;
  focusOutline: string;
};

export function computeAmbientPresence(
  context: NavigationContext,
  opts: {
    mode?: MissionControlMode;
    quietMode?: boolean;
    focusMode?: boolean;
    confidence?: number;
    resolvedTheme?: McResolvedTheme;
    accessibilityMode?: McAccessibilityMode;
  } = {},
): AmbientPresenceState {
  const {
    mode = "operator",
    quietMode = false,
    focusMode = false,
    confidence = 0.72,
    resolvedTheme = "dark",
    accessibilityMode = "standard",
  } = opts;

  let mood: AmbientMood = "stable";
  let attentionLevel: AttentionLevel = "passive";
  let rhythm: AmbientPresenceState["rhythm"] = "calm";

  if (context.hasAnomalies && confidence < 0.5) {
    mood = "critical";
    attentionLevel = "critical";
    rhythm = "alert";
  } else if (context.hasAnomalies || context.replayIntegrityDegraded) {
    mood = "elevated";
    attentionLevel = context.hasAnomalies ? "urgent" : "elevated";
    rhythm = "focused";
  } else if (context.hasActivePreflights || context.hasActiveJobs || confidence < 0.65) {
    mood = "informational";
    attentionLevel = "informational";
    rhythm = "focused";
  }

  if (quietMode || focusMode) {
    rhythm = "calm";
    if (mood !== "critical") attentionLevel = mood === "stable" ? "passive" : "informational";
  }

  if (mode === "executive" && mood !== "critical") {
    mood = mood === "elevated" ? "informational" : mood;
  }

  const palette = getThemeAmbientPalette(mood, resolvedTheme, accessibilityMode);
  const presenceLabel =
    mood === "stable"
      ? "Operational environment is calm and stable."
      : mood === "informational"
        ? "Ambient awareness — monitoring operational rhythm."
        : mood === "elevated"
          ? "Elevated concern — focused validation recommended."
          : "Critical focus — singular operational priority.";

  return {
    mood,
    attentionLevel,
    presenceLabel,
    rhythm,
    cssVars: {
      "--mc-ambient-tint": palette.tint,
      "--mc-ambient-glow": palette.glow,
      "--mc-ambient-sidebar": palette.sidebar,
      "--mc-ambient-focus": palette.focus,
    },
    shellStyle: {
      background: palette.background,
      transition: "background 0.6s ease, box-shadow 0.4s ease",
    },
    focusOutline: palette.focus,
  };
}

/** @deprecated legacy static palette — use getThemeAmbientPalette */
const AMBIENT_PALETTE: Record<
  AmbientMood,
  { tint: string; glow: string; sidebar: string; focus: string; background: string }
> = {
  stable: {
    tint: "rgba(148,163,184,0.04)",
    glow: "none",
    sidebar: "rgba(15,23,42,0.55)",
    focus: "rgba(34,211,238,0.12)",
    background: "linear-gradient(135deg, #050508 0%, #0f172a 48%, #050508 100%)",
  },
  informational: {
    tint: "rgba(59,130,246,0.05)",
    glow: "0 0 60px rgba(59,130,246,0.04)",
    sidebar: "rgba(15,23,42,0.62)",
    focus: "rgba(96,165,250,0.14)",
    background: "linear-gradient(135deg, #050508 0%, #0c1524 50%, #050508 100%)",
  },
  elevated: {
    tint: "rgba(251,191,36,0.05)",
    glow: "0 0 48px rgba(251,191,36,0.05)",
    sidebar: "rgba(24,20,12,0.55)",
    focus: "rgba(251,191,36,0.16)",
    background: "linear-gradient(135deg, #050508 0%, #14120c 50%, #050508 100%)",
  },
  critical: {
    tint: "rgba(248,113,113,0.06)",
    glow: "0 0 40px rgba(248,113,113,0.06)",
    sidebar: "rgba(24,12,12,0.55)",
    focus: "rgba(248,113,113,0.18)",
    background: "linear-gradient(135deg, #050508 0%, #1a0f0f 50%, #050508 100%)",
  },
};
