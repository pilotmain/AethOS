/** Phase 10.1.5.7 — Operational ergonomics — human-centered cognitive sustainability. */

import type { InvisibleCognitivePartnership } from "@/lib/missionControl/cognitivePartnership";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type OperationalErgonomicsState = {
  fatigueAwarePacing: boolean;
  calmReassurance: string | null;
  emotionalDecompression: boolean;
  confidenceRestraint: boolean;
  operationalEmpathy: string | null;
  narrativeSteadiness: string | null;
  ergonomicsClassName: string;
};

export function assessOperationalErgonomics(
  context: NavigationContext,
  partnership: InvisibleCognitivePartnership,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
    priorityIssue?: string;
  } = {},
): OperationalErgonomicsState {
  const { confidence = 0.72, recentlyResolved = false, priorityIssue } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { humanRealism, intelligence, serenity } = partnership;

  const fatigueAwarePacing = intelligence.emotionalStability.fatigueAwarePacing || intelligence.presence.cognitive.fatigueSensed;
  const emotionalDecompression = serenity.recoveryAtmosphere || intelligence.emotionalStability.recoveryDecompression;
  const confidenceRestraint = humanRealism.trustPacing || humanRealism.uncertaintyHonesty;

  const calmReassurance =
    humanRealism.calmReassurance ??
    (emotionalDecompression
      ? "Grounded reassurance — recovery progressing with cognitively respectful pacing."
      : null);

  const operationalEmpathy =
    context.replayIntegrityDegraded && !recentlyResolved
      ? "Operational empathy active — validation framed as collaborative prudence, not synthetic urgency."
      : humanRealism.supportiveTone;

  const narrativeSteadiness =
    (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : recentlyResolved
        ? "Operational confidence improved after reliability convergence, though extended-session replay validation is still recommended before broader rollout."
        : fatigueAwarePacing
          ? "Narrative steadiness preserved — guidance paced for sustainable investigation."
          : null;

  return {
    fatigueAwarePacing,
    calmReassurance,
    emotionalDecompression,
    confidenceRestraint,
    operationalEmpathy,
    narrativeSteadiness,
    ergonomicsClassName: [
      "mc-operational-ergonomics",
      emotionalDecompression ? "mc-ergonomics-recovery" : "",
      fatigueAwarePacing ? "mc-ergonomics-fatigue-aware" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
