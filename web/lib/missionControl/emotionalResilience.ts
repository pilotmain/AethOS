/** Phase 10.1.5.9 — Emotional operational resilience — sustained steadiness under complexity. */

import type { CalmOperationalConsciousness } from "@/lib/missionControl/operationalConsciousness";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type EmotionalResilienceState = {
  emotionalSteadiness: boolean;
  recoveryPacing: boolean;
  operationalReassurance: string | null;
  calmEscalation: boolean;
  cognitiveDecompression: boolean;
  operationalEmpathy: string | null;
  recoveryNarrative: string | null;
  resilienceClassName: string;
};

export function assessEmotionalResilience(
  context: NavigationContext,
  ops: CalmOperationalConsciousness,
  opts: { recentlyResolved?: boolean; confidence?: number } = {},
): EmotionalResilienceState {
  const { recentlyResolved = false, confidence = 0.72 } = opts;
  const { cognition, harmony, cognitiveErgonomics } = ops;
  const { calmComputing, partnership } = cognition;

  const recoveryPacing = recentlyResolved || harmony.recoveryAtmosphere || calmComputing.recoveryDecompression;
  const emotionalSteadiness =
    cognitiveErgonomics.emotionalSteadiness ||
    partnership.intelligence.emotionalStability.tensionBalance < 0.55;
  const calmEscalation = harmony.calmEscalation || partnership.intelligence.emotionalStability.calmEscalation;
  const cognitiveDecompression = recoveryPacing || cognitiveErgonomics.cognitiveDecompression;

  const recoveryNarrative = recoveryPacing
    ? "Operational stability improved after replay recovery. The environment is settling back into a calm operational rhythm."
    : null;

  const operationalReassurance = recoveryNarrative
    ? "Operational reassurance — emotional steadiness preserved through calm recovery pacing."
    : confidence >= 0.78 && !context.replayIntegrityDegraded
      ? "Operational reassurance — environmental steadiness supports sustained investigation."
      : harmony.atmosphericReassurance;

  const operationalEmpathy =
    context.replayIntegrityDegraded && !recentlyResolved
      ? "Operational empathy active — guidance remains emotionally steady, supportive, and cognitively respectful."
      : cognitiveErgonomics.operationalEmpathy;

  return {
    emotionalSteadiness,
    recoveryPacing,
    operationalReassurance,
    calmEscalation,
    cognitiveDecompression,
    operationalEmpathy,
    recoveryNarrative,
    resilienceClassName: [
      "mc-emotional-resilience",
      recoveryPacing ? "mc-resilience-recovery" : "",
      emotionalSteadiness ? "mc-resilience-steady" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
