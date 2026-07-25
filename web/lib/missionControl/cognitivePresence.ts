/** Phase 10.1.5.4 — Cognitive presence — load-aware operational calmness. */

import {
  computeOperationalEnvironment,
  type OperationalEnvironment,
} from "@/lib/missionControl/environmentalIntelligence";
import { assessInvisibleIntelligence, type InvisibleIntelligenceState } from "@/lib/missionControl/invisibleIntelligence";
import { assessEmotionalTrust, type EmotionalTrustState } from "@/lib/missionControl/emotionalTrust";
import { assessSpatialTrust, type SpatialTrustState } from "@/lib/missionControl/spatialTrust";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import type { McAccessibilityMode, McResolvedTheme } from "@/lib/missionControl/theme/operationalPalette";

export type CognitiveLoadLevel = "light" | "moderate" | "elevated" | "heavy";

export type CognitivePresenceState = {
  loadLevel: CognitiveLoadLevel;
  loadScore: number;
  fatigueSensed: boolean;
  focusContinuity: boolean;
  mentalPressureReduction: boolean;
  suppressSecondaryChrome: boolean;
  expandInvestigationOnly: boolean;
  compressLowConfidenceTelemetry: boolean;
  cognitiveWhisper: string;
};

export type CognitiveOperationalPresence = {
  environment: OperationalEnvironment;
  cognitive: CognitivePresenceState;
  invisible: InvisibleIntelligenceState;
  spatialTrust: SpatialTrustState;
  emotionalTrust: EmotionalTrustState;
  dominantThought: string | null;
  deepFocusActive: boolean;
  presenceWhisper: string;
  presenceClassName: string;
};

export function assessCognitivePresence(
  context: NavigationContext,
  environment: OperationalEnvironment,
  opts: {
    confidence?: number;
    quietMode?: boolean;
    focusMode?: boolean;
    recentlyResolved?: boolean;
  } = {},
): CognitivePresenceState {
  const { confidence = 0.72, quietMode = false, focusMode = false, recentlyResolved = false } = opts;

  let loadScore = 0.15;
  if (context.hasAnomalies) loadScore += 0.28;
  if (context.replayIntegrityDegraded) loadScore += 0.2;
  if (context.hasActivePreflights) loadScore += 0.12;
  if (context.hasActiveJobs) loadScore += 0.1;
  if ((context.pendingRecommendations ?? 0) > 2) loadScore += 0.08;
  if (confidence < 0.55) loadScore += 0.18;
  if (environment.pacing.tension >= 0.5) loadScore += 0.1;

  if (recentlyResolved || environment.pacing.recoveryCalming) loadScore = Math.min(loadScore, 0.28);
  if (quietMode) loadScore = Math.min(loadScore, 0.42);
  if (focusMode) loadScore = Math.min(loadScore, 0.38);

  loadScore = Math.min(0.95, loadScore);

  const loadLevel: CognitiveLoadLevel =
    loadScore >= 0.72 ? "heavy" : loadScore >= 0.48 ? "elevated" : loadScore >= 0.28 ? "moderate" : "light";

  const fatigueSensed =
    loadLevel === "heavy" || (loadLevel === "elevated" && Boolean(context.hasActiveJobs));
  const suppressSecondaryChrome = loadLevel !== "light" || focusMode || quietMode;
  const expandInvestigationOnly =
    loadLevel === "elevated" || loadLevel === "heavy" || environment.rhythm.expandActiveInvestigation;
  const compressLowConfidenceTelemetry = confidence < 0.65 || loadLevel !== "light";

  const cognitiveWhisper =
    loadLevel === "heavy"
      ? "Cognitive protection active — only the current investigation receives emphasis."
      : loadLevel === "elevated"
        ? "Operational pressure sensed — secondary chrome reduced for clarity."
        : focusMode
          ? "Deep focus workspace — minimal interruption surface."
          : "Cognitive load balanced — environment holding steady.";

  return {
    loadLevel,
    loadScore,
    fatigueSensed,
    focusContinuity: focusMode || quietMode || loadLevel === "elevated",
    mentalPressureReduction: suppressSecondaryChrome,
    suppressSecondaryChrome,
    expandInvestigationOnly,
    compressLowConfidenceTelemetry,
    cognitiveWhisper,
  };
}

export function resolveDominantThought(
  context: NavigationContext,
  cognitive: CognitivePresenceState,
  environment: OperationalEnvironment,
  opts: { priorityIssue?: string; recentlyResolved?: boolean } = {},
): string | null {
  const issue = opts.priorityIssue?.replace(/^the /i, "") ?? "operational validation";

  if (environment.pacing.recoveryCalming || opts.recentlyResolved) {
    return null;
  }

  if (environment.mood === "critical" || cognitive.loadLevel === "heavy") {
    return `Singular focus: ${issue} requires immediate validation before broader operational expansion.`;
  }

  if (
    cognitive.loadLevel === "elevated" ||
    environment.mood === "elevated" ||
    context.replayIntegrityDegraded
  ) {
    return `The highest-impact unresolved area right now is ${issue}.`;
  }

  if (cognitive.loadLevel === "moderate" && context.hasActivePreflights) {
    return "Governed engineering changes await review — preflight validation is the active thread.";
  }

  return null;
}

export function computeCognitiveOperationalPresence(
  context: NavigationContext,
  opts: {
    mode?: MissionControlMode;
    quietMode?: boolean;
    focusMode?: boolean;
    confidence?: number;
    recentlyResolved?: boolean;
    priorityIssue?: string;
    resolvedTheme?: McResolvedTheme;
    accessibilityMode?: McAccessibilityMode;
  } = {},
): CognitiveOperationalPresence {
  const environment = computeOperationalEnvironment(context, opts);
  const cognitive = assessCognitivePresence(context, environment, opts);
  const invisible = assessInvisibleIntelligence(context, cognitive, opts);
  const spatialTrust = assessSpatialTrust(context, environment, opts);
  const emotionalTrust = assessEmotionalTrust(context, opts);
  const dominantThought = resolveDominantThought(context, cognitive, environment, {
    priorityIssue: opts.priorityIssue,
    recentlyResolved: opts.recentlyResolved,
  });
  const deepFocusActive = Boolean(opts.focusMode) || cognitive.loadLevel === "heavy";

  const presenceWhisper = buildPresenceWhisper(cognitive, spatialTrust, environment, deepFocusActive);
  const presenceClassName = [
    environment.shellClassName,
    environment.canvasClassName,
    `mc-cognitive-${cognitive.loadLevel}`,
    deepFocusActive ? "mc-deep-focus" : "",
    invisible.smartQuietState ? "mc-invisible-quiet" : "",
    spatialTrust.trustClassName,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    environment,
    cognitive,
    invisible,
    spatialTrust,
    emotionalTrust,
    dominantThought,
    deepFocusActive,
    presenceWhisper,
    presenceClassName,
  };
}

function buildPresenceWhisper(
  cognitive: CognitivePresenceState,
  spatialTrust: SpatialTrustState,
  environment: OperationalEnvironment,
  deepFocusActive: boolean,
): string {
  if (deepFocusActive) {
    return "Deep operational workspace — intelligence working quietly in the background.";
  }
  if (spatialTrust.recoveryTransition) {
    return spatialTrust.trustWhisper;
  }
  if (cognitive.loadLevel === "elevated" || cognitive.loadLevel === "heavy") {
    return cognitive.cognitiveWhisper;
  }
  return spatialTrust.trustWhisper || environment.atmosphereWhisper;
}
