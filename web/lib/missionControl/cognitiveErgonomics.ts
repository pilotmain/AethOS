/** Phase 10.1.5.8 — Human cognitive ergonomics — long-session fatigue reduction. */

import type { AmbientCalmCognition } from "@/lib/missionControl/ambientCognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type CognitiveErgonomicsState = {
  fatigueAwarePacing: boolean;
  emotionalSteadiness: boolean;
  calmPhrasing: string | null;
  cognitiveDecompression: boolean;
  breathingRhythm: boolean;
  operationalEmpathy: string | null;
  companionPhrase: string | null;
  confidenceRestraint: boolean;
  ergonomicsClassName: string;
};

export function assessCognitiveErgonomics(
  context: NavigationContext,
  cognition: AmbientCalmCognition,
  opts: {
    priorityIssue?: string;
    recentlyResolved?: boolean;
    confidence?: number;
  } = {},
): CognitiveErgonomicsState {
  const { priorityIssue, recentlyResolved = false, confidence = 0.72 } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { ergonomics, calmComputing, partnership } = cognition;

  const fatigueAwarePacing = ergonomics.fatigueAwarePacing || cognition.ambientFlow.cognitiveRecoveryPacing;
  const emotionalSteadiness = partnership.humanRealism.emotionalSteadiness;
  const cognitiveDecompression = recentlyResolved || calmComputing.recoveryDecompression;
  const breathingRhythm = calmComputing.silenceWindow || cognition.ambientFlow.interruptionSuppressed;

  const calmPhrasing =
    ergonomics.calmReassurance ??
    (cognitiveDecompression
      ? "Calm operational phrasing — recovery communicated without pressure or overstatement."
      : null);

  const operationalEmpathy =
    context.replayIntegrityDegraded && !recentlyResolved
      ? "Operational empathy active — guidance remains steady, supportive, and cognitively respectful."
      : ergonomics.operationalEmpathy;

  const companionPhrase =
    (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : recentlyResolved || confidence >= 0.82
        ? "Operational confidence improved after reliability convergence, though extended-session replay validation is still recommended before broader rollout."
        : null;

  const confidenceRestraint =
    Boolean(context.replayIntegrityDegraded) ||
    (context.pendingRecommendations ?? 0) > 1 ||
    (confidence < 0.85 && !recentlyResolved);

  return {
    fatigueAwarePacing,
    emotionalSteadiness,
    calmPhrasing,
    cognitiveDecompression,
    breathingRhythm,
    operationalEmpathy,
    companionPhrase,
    confidenceRestraint,
    ergonomicsClassName: [
      "mc-cognitive-ergonomics",
      cognitiveDecompression ? "mc-ergonomics-decompression" : "",
      breathingRhythm ? "mc-ergonomics-breathing" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
