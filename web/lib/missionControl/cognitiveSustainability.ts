/** Phase 10.1.5.9 — Human cognitive sustainability & invisible human partnership. */

import type { CalmOperationalConsciousness } from "@/lib/missionControl/operationalConsciousness";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type CognitiveSustainabilityState = {
  fatigueAwarePacing: boolean;
  emotionalDecompression: boolean;
  confidenceRestraint: boolean;
  cognitiveRecoverySupport: boolean;
  breathingIntervals: boolean;
  calmInteraction: boolean;
  partnerPhrase: string | null;
  partnerHeadline: string | null;
  sustainabilityClassName: string;
};

export function assessCognitiveSustainability(
  context: NavigationContext,
  ops: CalmOperationalConsciousness,
  opts: {
    priorityIssue?: string;
    recentlyResolved?: boolean;
    confidence?: number;
  } = {},
): CognitiveSustainabilityState {
  const { priorityIssue, recentlyResolved = false, confidence = 0.72 } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { cognitiveErgonomics, cognition } = ops;
  const { calmComputing, ambientFlow } = cognition;

  const fatigueAwarePacing = cognitiveErgonomics.fatigueAwarePacing || ambientFlow.cognitiveRecoveryPacing;
  const emotionalDecompression = recentlyResolved || calmComputing.recoveryDecompression;
  const confidenceRestraint = cognitiveErgonomics.confidenceRestraint;
  const cognitiveRecoverySupport = emotionalDecompression || ambientFlow.cognitiveRecoveryPacing;
  const breathingIntervals = cognitiveErgonomics.breathingRhythm || calmComputing.silenceWindow;
  const calmInteraction = fatigueAwarePacing && !context.hasAnomalies;

  const partnerHeadline =
    (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : null;

  const partnerPhrase =
    partnerHeadline ??
    (recentlyResolved || confidence >= 0.82
      ? "Operational confidence improved after reliability convergence, though extended-session replay validation is still recommended before broader rollout."
      : fatigueAwarePacing
        ? "Invisible human partnership — guidance paced for sustainable long-session cognition."
        : null);

  return {
    fatigueAwarePacing,
    emotionalDecompression,
    confidenceRestraint,
    cognitiveRecoverySupport,
    breathingIntervals,
    calmInteraction,
    partnerPhrase,
    partnerHeadline,
    sustainabilityClassName: [
      "mc-cognitive-sustainability",
      "mc-invisible-partnership",
      emotionalDecompression ? "mc-sustainability-recovery" : "",
      breathingIntervals ? "mc-sustainability-breathing" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
