/** Phase 10.1.5.6 — Human realism — calm reassurance without manipulation. */

import type { InvisibleOperationalIntelligence } from "@/lib/missionControl/cognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type HumanRealismState = {
  calmReassurance: string | null;
  emotionalSteadiness: boolean;
  fatigueAwarePhrasing: string | null;
  supportiveTone: string | null;
  trustPacing: boolean;
  uncertaintyHonesty: boolean;
  companionPhrase: string | null;
};

export function assessHumanRealism(
  context: NavigationContext,
  intelligence: InvisibleOperationalIntelligence,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
    priorityIssue?: string;
  } = {},
): HumanRealismState {
  const { confidence = 0.72, recentlyResolved = false, priorityIssue } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { emotionalStability, presence, flow } = intelligence;

  const uncertaintyHonesty = Boolean(
    context.replayIntegrityDegraded || confidence < 0.78 || context.hasAnomalies,
  );
  const trustPacing = uncertaintyHonesty || presence.emotionalTrust.suppressOverclaiming;
  const emotionalSteadiness = emotionalStability.tensionBalance < 0.55 || flow.flowState === "recovering";

  const calmReassurance =
    recentlyResolved || emotionalStability.recoveryDecompression
      ? "Grounded reassurance — recovery progressing without dramatization or overstatement."
      : emotionalStability.cognitiveReassurance;

  const fatigueAwarePhrasing = emotionalStability.fatigueAwarePacing
    ? "Fatigue-aware phrasing — the environment paces guidance for sustainable cognition."
    : null;

  const supportiveTone =
    context.replayIntegrityDegraded && !recentlyResolved
      ? "Supportive operational tone — replay validation framed as prudent collaboration, not alarm."
      : emotionalStability.supportivePhrase;

  const companionPhrase =
    (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : recentlyResolved
        ? "Operational confidence improved after reliability convergence, though extended-session replay validation is still recommended before broader rollout."
        : null;

  return {
    calmReassurance,
    emotionalSteadiness,
    fatigueAwarePhrasing,
    supportiveTone,
    trustPacing,
    uncertaintyHonesty,
    companionPhrase,
  };
}
