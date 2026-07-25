/** Phase 10.1.5.12 — Operational signal hierarchy & cognitive focus energy. */

import type { CSSProperties } from "react";

export type OperationalSignalLevel =
  | "dominant"
  | "reassurance"
  | "continuity"
  | "whisper";

export const operationalSignalClass: Record<OperationalSignalLevel, string> = {
  dominant: "mc-signal-dominant",
  reassurance: "mc-signal-reassurance",
  continuity: "mc-signal-continuity",
  whisper: "mc-signal-whisper",
};

export const operationalSignalStyle: Record<OperationalSignalLevel, CSSProperties> = {
  dominant: {
    color: "var(--mc-text-strong, var(--mc-text))",
    fontWeight: 650,
    letterSpacing: "-0.025em",
  },
  reassurance: {
    color: "var(--mc-text-muted, #c4c4d0)",
    fontWeight: 450,
    fontSize: 15,
    lineHeight: 1.55,
  },
  continuity: {
    color: "var(--mc-text-muted, #c4c4d0)",
    fontWeight: 420,
    fontSize: 15,
    lineHeight: 1.6,
  },
  whisper: {
    color: "var(--mc-text-dim, #9a9aaa)",
    fontWeight: 400,
    fontSize: 13,
    lineHeight: 1.5,
    opacity: 0.92,
  },
};
