/** Phase 10.1.5.4 — Emotional trust — calm honesty without manipulation. */

import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type EmotionalTrustState = {
  honestyLevel: "full" | "calibrated";
  confidencePhrase: string;
  stabilityPhrase: string;
  reassurance: string | null;
  suppressOverclaiming: boolean;
};

export function assessEmotionalTrust(
  context: NavigationContext,
  opts: {
    confidence?: number;
    confidenceLabel?: string;
    recentlyResolved?: boolean;
    replayDegraded?: boolean;
  } = {},
): EmotionalTrustState {
  const {
    confidence = 0.72,
    confidenceLabel = "moderate",
    recentlyResolved = false,
    replayDegraded = false,
  } = opts;

  const uncertain = replayDegraded || confidence < 0.78 || context.hasAnomalies;
  const suppressOverclaiming = uncertain || confidenceLabel === "developing" || confidenceLabel === "limited";

  const confidencePhrase = suppressOverclaiming
    ? replayDegraded
      ? "Operational confidence is improving, though replay continuity still requires extended-session validation."
      : `Operational confidence is ${confidenceLabel} — validation recommended before broader rollout.`
    : recentlyResolved
      ? "Operational stability improved after replay recovery, though long-session validation is still recommended before broader rollout."
      : `Operational confidence is ${confidenceLabel} and holding steady across monitored surfaces.`;

  const stabilityPhrase =
    recentlyResolved || (confidence >= 0.82 && !context.hasAnomalies)
      ? "Operational stability improved after replay recovery, though long-session validation is still recommended before broader rollout."
      : context.hasAnomalies
        ? "Operational stability is intact at the system level — localized validation is the prudent next step."
        : "Operational stability remains intact — the environment is holding a calm baseline.";

  const reassurance =
    recentlyResolved || (confidence >= 0.82 && !replayDegraded)
      ? "Grounded reassurance — recovery is progressing without overstating certainty."
      : null;

  return {
    honestyLevel: suppressOverclaiming ? "calibrated" : "full",
    confidencePhrase,
    stabilityPhrase,
    reassurance,
    suppressOverclaiming,
  };
}
