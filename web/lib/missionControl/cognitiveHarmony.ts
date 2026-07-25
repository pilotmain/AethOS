/** Phase 10.1.5.8 — Cognitive harmony — emotional and cognitive environmental balance. */

import type { AmbientCalmCognition } from "@/lib/missionControl/ambientCognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type CognitiveHarmonyState = {
  emotionalPacing: boolean;
  operationalHarmony: boolean;
  environmentalSteadiness: boolean;
  recoveryAtmosphere: boolean;
  calmEscalation: boolean;
  atmosphericReassurance: string | null;
  harmonyPhrase: string;
  recoveryPhrase: string | null;
  harmonyClassName: string;
};

export function assessCognitiveHarmony(
  context: NavigationContext,
  cognition: AmbientCalmCognition,
  opts: { recentlyResolved?: boolean; confidence?: number } = {},
): CognitiveHarmonyState {
  const { recentlyResolved = false, confidence = 0.72 } = opts;
  const { calmComputing, partnership, ergonomics } = cognition;

  const recoveryAtmosphere = recentlyResolved || calmComputing.recoveryDecompression;
  const environmentalSteadiness = calmComputing.atmosphericSteadiness || cognition.partnership.trustPresence.operationalSteadiness.length > 0;
  const emotionalPacing = calmComputing.calmEscalationPacing || ergonomics.fatigueAwarePacing;
  const operationalHarmony = environmentalSteadiness && !context.hasAnomalies;
  const calmEscalation = partnership.intelligence.emotionalStability.calmEscalation;

  const recoveryPhrase = recoveryAtmosphere
    ? "Operational stability has improved after replay recovery. The environment is gradually returning to a steady operational rhythm."
    : null;

  const harmonyPhrase =
    recoveryPhrase ??
    (cognition.deepFocusEnvironment
      ? "Cognitive harmony active — environmental steadiness supporting uninterrupted thought."
      : "Operational harmony maintained — complexity harmonized without cognitive overload.");

  const atmosphericReassurance = recoveryAtmosphere
    ? "Atmospheric reassurance — trust continuity through calm recovery pacing."
    : confidence >= 0.78 && !context.replayIntegrityDegraded
      ? "Atmospheric reassurance — environmental steadiness holds a trustworthy baseline."
      : null;

  return {
    emotionalPacing,
    operationalHarmony,
    environmentalSteadiness,
    recoveryAtmosphere,
    calmEscalation,
    atmosphericReassurance,
    harmonyPhrase,
    recoveryPhrase,
    harmonyClassName: [
      "mc-cognitive-harmony",
      recoveryAtmosphere ? "mc-harmony-recovery" : "",
      operationalHarmony ? "mc-harmony-steady" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
