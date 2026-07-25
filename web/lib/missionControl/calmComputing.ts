/** Phase 10.1.5.7 — Calm computing atmosphere — emotional stabilization of operational work. */

import type { InvisibleCognitivePartnership } from "@/lib/missionControl/cognitivePartnership";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type CalmComputingState = {
  environmentalCalmness: boolean;
  atmosphericSteadiness: boolean;
  recoveryDecompression: boolean;
  silenceWindow: boolean;
  trustContinuity: boolean;
  calmEscalationPacing: boolean;
  calmPhrase: string;
  recoveryPhrase: string | null;
  computingClassName: string;
};

export function assessCalmComputing(
  context: NavigationContext,
  partnership: InvisibleCognitivePartnership,
  opts: { recentlyResolved?: boolean; confidence?: number } = {},
): CalmComputingState {
  const { recentlyResolved = false, confidence = 0.72 } = opts;
  const { serenity, trustPresence, intelligence } = partnership;

  const recoveryDecompression = recentlyResolved || serenity.recoveryAtmosphere;
  const silenceWindow = serenity.silentInterval || intelligence.flow.operationalSilenceWindow;
  const atmosphericSteadiness = trustPresence.atmosphericStability.length > 0 || serenity.calmPacing;
  const environmentalCalmness = serenity.tensionReduced || partnership.humanRealism.emotionalSteadiness;
  const trustContinuity = trustPresence.recoveryTransition || confidence >= 0.75;
  const calmEscalationPacing =
    intelligence.emotionalStability.calmEscalation || serenity.urgencyBalanced;

  const recoveryPhrase = recoveryDecompression
    ? "Operational stability improved after replay recovery. The environment is settling back into a steady operational state."
    : null;

  const calmPhrase = recoveryPhrase ??
    (silenceWindow
      ? "Calm computing active — operational silence window preserving cognitive breathing room."
      : environmentalCalmness
        ? "Environmental calmness maintained — atmospheric steadiness supports sustained clarity."
        : "Calm computing baseline — trust continuity through restrained environmental behavior.");

  return {
    environmentalCalmness,
    atmosphericSteadiness,
    recoveryDecompression,
    silenceWindow,
    trustContinuity,
    calmEscalationPacing,
    calmPhrase,
    recoveryPhrase,
    computingClassName: [
      "mc-calm-computing",
      recoveryDecompression ? "mc-calm-recovery" : "",
      silenceWindow ? "mc-calm-silence" : "",
      atmosphericSteadiness ? "mc-calm-steady" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
