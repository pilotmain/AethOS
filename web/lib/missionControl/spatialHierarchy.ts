/** Phase 10.1.5.1 — Spatial hierarchy, attention gradients, calm typography. */

import type { CSSProperties } from "react";

import { mcColors } from "@/lib/missionControl/layout";

export type SpatialLayer = "primary" | "secondary" | "tertiary" | "background";

export type AttentionLevel =
  | "invisible"
  | "silent"
  | "atmospheric"
  | "whisper"
  | "passive"
  | "informational"
  | "contextual"
  | "elevated"
  | "urgent"
  | "critical";

/** Phase 10.1.5.5+10.1.5.6 — Calm / cognitive attention architecture. */
export type CalmAttentionLevel = AttentionLevel;
export type CognitiveAttentionLevel = AttentionLevel;
/** Phase 10.1.5.7 — Protected attention for cognitive clarity. */
export type ProtectedAttentionLevel = AttentionLevel;
/** Phase 10.1.5.8 — Harmonious attention for cognitive protection. */
export type HarmoniousAttentionLevel = AttentionLevel;
/** Phase 10.1.5.9 — Sanctuary attention for cognitive restraint. */
export type SanctuaryAttentionLevel = AttentionLevel;

export function resolveCalmAttention(input: {
  mood: string;
  flowState: string;
  recovery: boolean;
  tension: number;
}): CalmAttentionLevel {
  return resolveCognitiveAttention({ ...input, deepSerenity: false });
}

/** Phase 10.1.5.6 — Cognitive attention with whisper-level ambient awareness. */
export function resolveCognitiveAttention(input: {
  mood: string;
  flowState: string;
  recovery: boolean;
  tension: number;
  deepSerenity?: boolean;
}): CognitiveAttentionLevel {
  return resolveProtectedAttention({
    mood: input.mood,
    flowState: input.flowState,
    recovery: input.recovery,
    tension: input.tension,
    deepFocus: input.deepSerenity,
  });
}

/** Phase 10.1.5.7 — Cognitive attention protection with atmospheric awareness. */
export function resolveProtectedAttention(input: {
  mood: string;
  flowState: string;
  recovery: boolean;
  tension: number;
  deepFocus?: boolean;
}): ProtectedAttentionLevel {
  return resolveHarmoniousAttention({
    mood: input.mood,
    consciousnessState: input.recovery ? "restoring" : input.deepFocus ? "immersive" : input.flowState,
    recovery: input.recovery,
    tension: input.tension,
    deepImmersion: input.deepFocus,
  });
}

/** Phase 10.1.5.8 — Cognitive attention harmony with invisible suppression. */
export function resolveHarmoniousAttention(input: {
  mood: string;
  consciousnessState: string;
  recovery: boolean;
  tension: number;
  deepImmersion?: boolean;
}): HarmoniousAttentionLevel {
  return resolveSanctuaryAttention({
    mood: input.mood,
    sanctuaryState:
      input.recovery || input.consciousnessState === "restoring"
        ? "restoring"
        : input.deepImmersion || input.consciousnessState === "immersive"
          ? "immersive"
          : input.consciousnessState === "focused"
            ? "protected"
            : input.consciousnessState === "aware"
              ? "grounded"
              : "resting",
    recovery: input.recovery,
    tension: input.tension,
    sanctuaryImmersion: input.deepImmersion,
  });
}

/** Phase 10.1.5.9 — Cognitive attention sanctuary — one concern dominates cognition. */
export function resolveSanctuaryAttention(input: {
  mood: string;
  sanctuaryState: string;
  recovery: boolean;
  tension: number;
  sanctuaryImmersion?: boolean;
}): SanctuaryAttentionLevel {
  if (input.recovery || input.sanctuaryState === "restoring") return "invisible";
  if (input.sanctuaryImmersion || input.sanctuaryState === "immersive") return "invisible";
  if (input.sanctuaryState === "protected" && input.tension < 0.42) return "whisper";
  if (input.sanctuaryState === "grounded") return "atmospheric";
  if (input.mood === "critical" && input.tension >= 0.78) return "critical";
  if (input.mood === "critical" || input.tension >= 0.78) return "urgent";
  if (input.mood === "elevated" || input.tension >= 0.52) return "elevated";
  if (input.tension >= 0.38 || input.sanctuaryState === "protected") return "contextual";
  if (input.mood === "informational" || input.sanctuaryState === "resting") return "informational";
  return "whisper";
}

export const spatialLayerStyle: Record<SpatialLayer, CSSProperties> = {
  primary: {
    padding: "48px 52px",
    marginBottom: 48,
    borderRadius: 20,
    border: "1px solid var(--mc-border, rgba(255,255,255,0.16))",
    background: "var(--mc-surface-primary, #12121c)",
    boxShadow: "0 1px 2px rgba(0,0,0,0.12), 0 12px 32px rgba(0,0,0,0.18)",
  },
  secondary: {
    padding: "22px 28px",
    marginBottom: 24,
    borderRadius: 16,
    border: "1px solid var(--mc-border-subtle, rgba(255,255,255,0.10))",
    background: "var(--mc-bg-card, #14141f)",
    boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
  },
  tertiary: {
    padding: "16px 20px",
    marginBottom: 16,
    borderRadius: 14,
    border: "1px solid rgba(255,255,255,0.035)",
    background: "rgba(0,0,0,0.12)",
  },
  background: {
    padding: "14px 18px",
    marginBottom: 12,
    borderRadius: 12,
    border: "none",
    background: "transparent",
  },
};

export function primaryFocusStyle(focusOutline: string, depthShadow?: string): CSSProperties {
  return {
    ...spatialLayerStyle.primary,
    boxShadow: `${depthShadow ?? "0 1px 2px rgba(0,0,0,0.12), 0 12px 32px rgba(0,0,0,0.18)"}, inset 0 0 0 1px ${focusOutline}`,
  };
}

/** Ultra-calm attention — only one level should dominate visually. */
export function dominantAttentionLevel(levels: AttentionLevel[]): AttentionLevel {
  const rank: Record<AttentionLevel, number> = {
    invisible: -2,
    silent: -1,
    atmospheric: 0,
    whisper: 1,
    passive: 2,
    informational: 3,
    contextual: 4,
    elevated: 5,
    urgent: 6,
    critical: 7,
  };
  return levels.reduce((best, current) => (rank[current] > rank[best] ? current : best), "invisible");
}

export const attentionPalette: Record<
  AttentionLevel,
  { color: string; bg: string; border: string; glow?: string }
> = {
  invisible: {
    color: "transparent",
    bg: "transparent",
    border: "transparent",
  },
  silent: {
    color: mcColors.textDim,
    bg: "transparent",
    border: "transparent",
  },
  atmospheric: {
    color: mcColors.textDim,
    bg: "rgba(255,255,255,0.015)",
    border: "rgba(255,255,255,0.03)",
  },
  whisper: {
    color: mcColors.textDim,
    bg: "rgba(255,255,255,0.02)",
    border: "rgba(255,255,255,0.04)",
  },
  passive: {
    color: mcColors.textMuted,
    bg: "transparent",
    border: mcColors.borderSubtle,
  },
  informational: {
    color: "#93c5fd",
    bg: "rgba(59,130,246,0.06)",
    border: "rgba(59,130,246,0.18)",
  },
  contextual: {
    color: "#fcd34d",
    bg: "rgba(251,191,36,0.05)",
    border: "rgba(251,191,36,0.15)",
  },
  elevated: {
    color: "#fde68a",
    bg: "rgba(251,191,36,0.07)",
    border: "rgba(251,191,36,0.2)",
  },
  urgent: {
    color: "#fca5a5",
    bg: "rgba(248,113,113,0.06)",
    border: "rgba(248,113,113,0.18)",
  },
  critical: {
    color: "#fecaca",
    bg: "rgba(248,113,113,0.1)",
    border: "rgba(248,113,113,0.28)",
    glow: "0 0 20px rgba(248,113,113,0.12)",
  },
};

export function attentionChipStyle(level: AttentionLevel): CSSProperties {
  const p = attentionPalette[level];
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.02em",
    color: p.color,
    background: p.bg,
    border: `1px solid ${p.border}`,
    boxShadow: p.glow,
  };
}

export const calmTypography = {
  focusTitle: {
    margin: 0,
    fontSize: 24,
    fontWeight: 650,
    lineHeight: 1.3,
    letterSpacing: "-0.025em",
    color: "var(--mc-text-strong, #ffffff)",
  } satisfies CSSProperties,
  focusLead: {
    margin: "12px 0 0",
    fontSize: 16,
    lineHeight: 1.55,
    fontWeight: 450,
    color: "var(--mc-text-muted, #c4c4d0)",
    maxWidth: 720,
  } satisfies CSSProperties,
  sectionLabel: {
    margin: 0,
    fontSize: 11,
    fontWeight: 650,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: "var(--mc-text-dim, #9a9aaa)",
  },
  body: {
    margin: 0,
    fontSize: 15,
    lineHeight: 1.6,
    fontWeight: 420,
    color: "var(--mc-text-muted, #c4c4d0)",
    whiteSpace: "pre-wrap" as const,
  },
  meta: {
    fontSize: 13,
    lineHeight: 1.5,
    fontWeight: 400,
    color: "var(--mc-text-dim, #9a9aaa)",
  },
};

export function confidenceLabel(score: number): string {
  if (score >= 0.8) return "strong";
  if (score >= 0.65) return "moderate";
  if (score >= 0.5) return "developing";
  return "limited";
}
