/** Phase 10.1.5.5 — Invisible operational assistance — quiet help without attention-seeking. */

import type { CognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import type { CognitiveFlowState } from "@/lib/missionControl/cognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type InvisibleAssistanceState = {
  passiveGuidance: string | null;
  contextualPrioritization: boolean;
  recommendationRestraint: boolean;
  silentSimplification: boolean;
  backgroundIntelligence: boolean;
  operationalAnticipation: string | null;
  suppressAttentionSeeking: boolean;
  maxVisibleSurfaces: number;
  hideWhisperChrome: boolean;
};

export function assessInvisibleAssistance(
  context: NavigationContext,
  presence: CognitiveOperationalPresence,
  flow: CognitiveFlowState,
  opts: {
    focusMode?: boolean;
    quietMode?: boolean;
    confidence?: number;
  } = {},
): InvisibleAssistanceState {
  const { focusMode = false, quietMode = false, confidence = 0.72 } = opts;
  const { invisible, cognitive } = presence;

  const silentSimplification =
    flow.preserveMomentum || invisible.adaptiveSimplification || focusMode || quietMode;
  const recommendationRestraint =
    flow.pauseWeakRecommendations || invisible.suppressWeakRecommendations || confidence < 0.65;
  const contextualPrioritization =
    context.replayIntegrityDegraded || cognitive.loadLevel !== "light" || flow.flowState === "investigating";

  let maxVisibleSurfaces = invisible.maxSurfaces;
  if (flow.flowState === "immersed") maxVisibleSurfaces = 1;
  else if (flow.flowState === "investigating") maxVisibleSurfaces = Math.min(maxVisibleSurfaces, 2);

  const passiveGuidance =
    flow.flowState === "immersed"
      ? "Intelligence working invisibly — only the primary investigation remains visible."
      : contextualPrioritization && context.replayIntegrityDegraded
        ? "The highest-impact unresolved area right now is replay continuity during extended operational sessions."
        : flow.operationalSilenceWindow
          ? null
          : silentSimplification
            ? "Quiet assistance active — non-essential guidance held in the background."
            : null;

  const operationalAnticipation =
    context.hasActivePreflights && !focusMode
      ? "Preflight validation is the natural next thread when you are ready."
      : context.replayIntegrityDegraded && !flow.operationalSilenceWindow
        ? "Extended-session replay validation remains the highest-impact follow-up."
        : null;

  return {
    passiveGuidance,
    contextualPrioritization,
    recommendationRestraint,
    silentSimplification,
    backgroundIntelligence: flow.flowState !== "sustained" || invisible.smartQuietState,
    operationalAnticipation,
    suppressAttentionSeeking: silentSimplification || flow.operationalSilenceWindow,
    maxVisibleSurfaces,
    hideWhisperChrome: flow.operationalSilenceWindow && focusMode,
  };
}
