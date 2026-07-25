/** Phase 10.1.5.3 — Living operational rhythm — atmospheric motion and compression. */

import type { AmbientMood } from "@/lib/missionControl/ambientPresence";
import type { EmotionalPacingState } from "@/lib/missionControl/emotionalPacing";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

export type LivingRhythmState = {
  tempo: "slow" | "medium" | "steady";
  tempoMs: number;
  breathe: boolean;
  ambientPulse: boolean;
  compressInactive: boolean;
  expandActiveInvestigation: boolean;
  hoverPhysics: "soft" | "minimal";
};

export function deriveLivingRhythm(
  mood: AmbientMood,
  pacing: EmotionalPacingState,
  opts: {
    mode?: MissionControlMode;
    quietMode?: boolean;
    focusMode?: boolean;
  } = {},
): LivingRhythmState {
  const { quietMode = false, focusMode = false } = opts;

  const tempo: LivingRhythmState["tempo"] =
    mood === "critical" ? "steady" : quietMode || focusMode || pacing.recoveryCalming ? "slow" : "medium";

  const tempoMs = tempo === "slow" ? 7200 : tempo === "medium" ? 5600 : 4800;

  return {
    tempo,
    tempoMs,
    breathe: mood !== "critical" && !focusMode,
    ambientPulse: mood === "informational" || mood === "elevated",
    compressInactive: focusMode || quietMode || pacing.focusPreservation,
    expandActiveInvestigation: mood === "elevated" || mood === "critical" || pacing.escalation === "focused",
    hoverPhysics: quietMode ? "minimal" : "soft",
  };
}

export function rhythmClassNames(rhythm: LivingRhythmState): string {
  const parts = [`mc-rhythm-${rhythm.tempo}`];
  if (rhythm.breathe) parts.push("mc-breathe");
  if (rhythm.ambientPulse) parts.push("mc-ambient-pulse");
  if (rhythm.compressInactive) parts.push("mc-compress-inactive");
  if (rhythm.expandActiveInvestigation) parts.push("mc-expand-investigation");
  if (rhythm.hoverPhysics === "minimal") parts.push("mc-hover-minimal");
  return parts.join(" ");
}
