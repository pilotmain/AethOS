/** Phase 10.1.5.3 — Environmental intelligence — living operational atmosphere. */

import type { CSSProperties } from "react";

import { computeAmbientPresence, type AmbientMood } from "@/lib/missionControl/ambientPresence";
import { assessEmotionalPacing, type EmotionalPacingState } from "@/lib/missionControl/emotionalPacing";
import { deriveLivingRhythm, type LivingRhythmState } from "@/lib/missionControl/livingRhythm";
import type { AttentionLevel } from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import type { McAccessibilityMode, McResolvedTheme } from "@/lib/missionControl/theme/operationalPalette";

export type OperationalAtmosphere = "cool-quiet" | "aware" | "warm-focus" | "restrained-urgency";

export type OperationalEnvironment = {
  atmosphere: OperationalAtmosphere;
  mood: AmbientMood;
  attentionLevel: AttentionLevel;
  presenceLabel: string;
  atmosphereWhisper: string;
  pacing: EmotionalPacingState;
  rhythm: LivingRhythmState;
  cssVars: Record<string, string>;
  shellStyle: CSSProperties;
  focusOutline: string;
  canvasClassName: string;
  shellClassName: string;
};

export function computeOperationalEnvironment(
  context: NavigationContext,
  opts: {
    mode?: MissionControlMode;
    quietMode?: boolean;
    focusMode?: boolean;
    confidence?: number;
    recentlyResolved?: boolean;
    resolvedTheme?: McResolvedTheme;
    accessibilityMode?: McAccessibilityMode;
  } = {},
): OperationalEnvironment {
  const { confidence = 0.72, recentlyResolved = false } = opts;
  const ambient = computeAmbientPresence(context, opts);
  const pacing = assessEmotionalPacing(context, {
    confidence,
    quietMode: opts.quietMode,
    focusMode: opts.focusMode,
    recentlyResolved,
  });
  const rhythm = deriveLivingRhythm(ambient.mood, pacing, opts);

  const atmosphere = mapAtmosphere(ambient.mood, pacing.tension);
  const atmosphereWhisper = buildAtmosphereWhisper(atmosphere, pacing);

  const depthBoost =
    atmosphere === "warm-focus" ? "0 24px 64px rgba(0,0,0,0.26)" : "0 20px 56px rgba(0,0,0,0.22)";

  return {
    atmosphere,
    mood: ambient.mood,
    attentionLevel: resolveAttentionLevel(ambient.attentionLevel, pacing),
    presenceLabel: ambient.presenceLabel,
    atmosphereWhisper,
    pacing,
    rhythm,
    cssVars: {
      ...ambient.cssVars,
      "--mc-atmosphere-depth": depthBoost,
      "--mc-rhythm-tempo": `${rhythm.tempoMs}ms`,
      "--mc-emotional-tension": String(pacing.tension),
    },
    shellStyle: {
      ...ambient.shellStyle,
      boxShadow: atmosphere === "restrained-urgency" ? "inset 0 0 80px rgba(248,113,113,0.03)" : undefined,
    },
    focusOutline: ambient.focusOutline,
    canvasClassName: `mc-living-atmosphere mc-rhythm-${rhythm.tempo} ${rhythm.breathe ? "mc-breathe" : ""}`.trim(),
    shellClassName: `mc-ambient-shell mc-atmosphere-${atmosphere}`,
  };
}

function mapAtmosphere(mood: AmbientMood, tension: number): OperationalAtmosphere {
  if (mood === "critical") return "restrained-urgency";
  if (mood === "elevated" || tension >= 0.55) return "warm-focus";
  if (mood === "informational") return "aware";
  return "cool-quiet";
}

function buildAtmosphereWhisper(atmosphere: OperationalAtmosphere, pacing: EmotionalPacingState): string {
  if (pacing.recoveryCalming) {
    return "Operational confidence improved. The environment is returning to a stable state.";
  }
  switch (atmosphere) {
    case "cool-quiet":
      return "Living operational space — cool, quiet, and breathable.";
    case "aware":
      return "Ambient awareness active — calm monitoring without interruption pressure.";
    case "warm-focus":
      return "Warm undertone — gentle emphasis on the highest-impact validation area.";
    case "restrained-urgency":
      return "Singular operational focus — clarity without panic.";
    default:
      return pacing.pacingNote;
  }
}

function resolveAttentionLevel(base: AttentionLevel, pacing: EmotionalPacingState): AttentionLevel {
  if (pacing.recoveryCalming) return "passive";
  if (pacing.tension >= 0.7) return "urgent";
  if (pacing.tension >= 0.45) return "contextual";
  return base;
}
