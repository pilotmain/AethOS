/** Phase 10.1.5.7 — Invisible operational guidance — quiet steering without attention competition. */

import type { InvisibleCognitivePartnership } from "@/lib/missionControl/cognitivePartnership";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

type AmbientFlowGuidanceInput = {
  investigationImmersion: boolean;
  interruptionSuppressed: boolean;
  deepFocusEnvironment: boolean;
  contextualSimplification: boolean;
};

export type InvisibleGuidanceState = {
  passivePrioritization: boolean;
  contextualSteering: boolean;
  recommendationMinimized: boolean;
  environmentalCue: string | null;
  narrativeHint: string | null;
  intelligentSilence: boolean;
  guidanceWhisper: string | null;
  maxSurfaces: number;
};

export function assessInvisibleGuidance(
  context: NavigationContext,
  partnership: InvisibleCognitivePartnership,
  ambientFlow: AmbientFlowGuidanceInput,
  opts: { priorityIssue?: string; focusMode?: boolean } = {},
): InvisibleGuidanceState {
  const issue = opts.priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { intelligence, partnership: partner } = partnership;
  const { flow, assistance } = intelligence;

  const passivePrioritization =
    context.replayIntegrityDegraded || ambientFlow.investigationImmersion || partner.investigationAwareness;
  const recommendationMinimized =
    partner.attentionPressureBalanced || flow.pauseWeakRecommendations || assistance.recommendationRestraint;
  const intelligentSilence = ambientFlow.interruptionSuppressed || flow.operationalSilenceWindow;
  const contextualSteering = passivePrioritization && !intelligentSilence;

  let maxSurfaces = assistance.maxVisibleSurfaces;
  if (ambientFlow.deepFocusEnvironment) maxSurfaces = 1;
  else if (ambientFlow.contextualSimplification) maxSurfaces = Math.min(maxSurfaces, 2);

  const environmentalCue = intelligentSilence
    ? null
    : passivePrioritization
      ? "Environmental directional cue — investigation context remains the natural orientation."
      : null;

  const narrativeHint =
    (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : contextualSteering && context.replayIntegrityDegraded
        ? "Extended-session replay validation remains the highest-impact follow-up when you are ready."
        : null;

  const guidanceWhisper = intelligentSilence
    ? null
    : narrativeHint ??
      (passivePrioritization
        ? "Invisible guidance active — attention shaped quietly, not demanded."
        : "Operational guidance held in the background until relevance increases.");

  return {
    passivePrioritization,
    contextualSteering,
    recommendationMinimized,
    environmentalCue,
    narrativeHint,
    intelligentSilence,
    guidanceWhisper,
    maxSurfaces,
  };
}
