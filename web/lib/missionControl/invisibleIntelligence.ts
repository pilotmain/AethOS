/** Phase 10.1.5.4 — Invisible intelligence — quiet simplification without announcement. */

import type { CognitivePresenceState } from "@/lib/missionControl/cognitivePresence";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type InvisibleIntelligenceState = {
  suppressLowValueSurfaces: boolean;
  suppressWeakRecommendations: boolean;
  adaptiveSimplification: boolean;
  smartQuietState: boolean;
  maxSurfaces: number;
  silenceNote: string | null;
  relevanceWeight: number;
  batchRecommendations: boolean;
  delaySecondaryUpdates: boolean;
};

export function assessInvisibleIntelligence(
  context: NavigationContext,
  cognitive: CognitivePresenceState,
  opts: {
    quietMode?: boolean;
    focusMode?: boolean;
    confidence?: number;
  } = {},
): InvisibleIntelligenceState {
  const { quietMode = false, focusMode = false, confidence = 0.72 } = opts;

  const highLoad = cognitive.loadLevel === "elevated" || cognitive.loadLevel === "heavy";
  const suppressWeakRecommendations =
    highLoad ||
    focusMode ||
    (context.pendingRecommendations ?? 0) <= 1 ||
    confidence < 0.6;

  const adaptiveSimplification = highLoad || quietMode || focusMode || cognitive.fatigueSensed;
  const suppressLowValueSurfaces = adaptiveSimplification || confidence < 0.55;

  let maxSurfaces = 4;
  if (focusMode) maxSurfaces = 2;
  else if (quietMode || highLoad) maxSurfaces = 3;
  else if (cognitive.loadLevel === "moderate") maxSurfaces = 3;

  const relevanceWeight =
    cognitive.loadLevel === "heavy" ? 0.92 : cognitive.loadLevel === "elevated" ? 0.78 : 0.55;

  const smartQuietState = focusMode || (quietMode && !context.hasAnomalies) || cognitive.mentalPressureReduction;

  const silenceNote = smartQuietState
    ? focusMode
      ? "Invisible intelligence — holding non-essential surfaces until you expand depth."
      : "Quiet guidance — only high-relevance context is visible."
    : null;

  return {
    suppressLowValueSurfaces,
    suppressWeakRecommendations,
    adaptiveSimplification,
    smartQuietState,
    maxSurfaces,
    silenceNote,
    relevanceWeight,
    batchRecommendations: focusMode || highLoad,
    delaySecondaryUpdates: focusMode || cognitive.fatigueSensed,
  };
}
