/** Phase 10.1.5.5 — Cognitive flow — uninterrupted operational thinking. */

import type { CognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import { computeCognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import { assessEmotionalStability, type EmotionalStabilityState } from "@/lib/missionControl/emotionalStability";
import { assessInvisibleAssistance, type InvisibleAssistanceState } from "@/lib/missionControl/invisibleAssistance";
import { assessTrustAtmosphere, type TrustAtmosphereState } from "@/lib/missionControl/trustAtmosphere";
import type { CalmAttentionLevel } from "@/lib/missionControl/spatialHierarchy";
import { resolveCalmAttention } from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type FlowState = "sustained" | "investigating" | "immersed" | "recovering";

export type CognitiveFlowState = {
  flowState: FlowState;
  interruptionCost: number;
  preserveMomentum: boolean;
  suppressSecondaryDomains: boolean;
  pauseWeakRecommendations: boolean;
  minimizeMotion: boolean;
  reduceEnvironmentalVariation: boolean;
  enlargeInvestigationNarrative: boolean;
  operationalSilenceWindow: boolean;
  flowWhisper: string;
};

export type InvisibleOperationalIntelligence = {
  presence: CognitiveOperationalPresence;
  flow: CognitiveFlowState;
  assistance: InvisibleAssistanceState;
  trustAtmosphere: TrustAtmosphereState;
  emotionalStability: EmotionalStabilityState;
  calmAttention: CalmAttentionLevel;
  immersionActive: boolean;
  intelligenceWhisper: string;
  intelligenceClassName: string;
  whisperLevel: "silent" | "passive" | "normal";
};

export function assessCognitiveFlow(
  context: NavigationContext,
  presence: CognitiveOperationalPresence,
  opts: {
    focusMode?: boolean;
    quietMode?: boolean;
    recentlyResolved?: boolean;
  } = {},
): CognitiveFlowState {
  const { focusMode = false, quietMode = false, recentlyResolved = false } = opts;
  const { cognitive, environment, deepFocusActive } = presence;

  let interruptionCost = 0.12;
  if (context.hasActiveJobs) interruptionCost += 0.1;
  if ((context.pendingRecommendations ?? 0) > 1) interruptionCost += 0.14;
  if (context.hasActivePreflights) interruptionCost += 0.08;
  if (environment.mood === "elevated" || environment.mood === "critical") interruptionCost += 0.12;

  if (focusMode || deepFocusActive) interruptionCost = Math.min(interruptionCost, 0.22);
  if (recentlyResolved || environment.pacing.recoveryCalming) interruptionCost = Math.min(interruptionCost, 0.18);

  interruptionCost = Math.min(0.88, interruptionCost);

  const investigating =
    context.replayIntegrityDegraded ||
    cognitive.loadLevel === "elevated" ||
    cognitive.loadLevel === "heavy" ||
    environment.mood === "elevated";

  const flowState: FlowState = recentlyResolved || environment.pacing.recoveryCalming
    ? "recovering"
    : focusMode || deepFocusActive
      ? "immersed"
      : investigating
        ? "investigating"
        : "sustained";

  const highFlowProtection = flowState === "immersed" || flowState === "investigating" || interruptionCost >= 0.35;

  const flowWhisper =
    flowState === "immersed"
      ? "Cognitive flow protected — investigation immersion active."
      : flowState === "investigating"
        ? "Operational flow sustained — secondary interruption surfaces suppressed."
        : flowState === "recovering"
          ? "Flow recovering — environmental variation minimized."
          : "Uninterrupted cognitive flow — environment holding steady.";

  return {
    flowState,
    interruptionCost,
    preserveMomentum: highFlowProtection || quietMode,
    suppressSecondaryDomains: highFlowProtection || cognitive.suppressSecondaryChrome,
    pauseWeakRecommendations: highFlowProtection || presence.invisible.suppressWeakRecommendations,
    minimizeMotion: flowState === "immersed" || focusMode || quietMode,
    reduceEnvironmentalVariation: highFlowProtection || recentlyResolved,
    enlargeInvestigationNarrative: investigating || deepFocusActive,
    operationalSilenceWindow: flowState === "immersed" || (quietMode && !context.hasAnomalies),
    flowWhisper,
  };
}

export function computeInvisibleOperationalIntelligence(
  context: NavigationContext,
  opts: {
    mode?: MissionControlMode;
    quietMode?: boolean;
    focusMode?: boolean;
    confidence?: number;
    recentlyResolved?: boolean;
    priorityIssue?: string;
    resolvedTheme?: import("@/lib/missionControl/theme/operationalPalette").McResolvedTheme;
    accessibilityMode?: import("@/lib/missionControl/theme/operationalPalette").McAccessibilityMode;
  } = {},
): InvisibleOperationalIntelligence {
  const presence = computeCognitiveOperationalPresence(context, opts);
  const flow = assessCognitiveFlow(context, presence, opts);
  const assistance = assessInvisibleAssistance(context, presence, flow, opts);
  const trustAtmosphere = assessTrustAtmosphere(context, presence, opts);
  const emotionalStability = assessEmotionalStability(context, presence, flow, opts);

  const immersionActive = flow.flowState === "immersed" || presence.deepFocusActive;
  const calmAttention = resolveCalmAttention({
    mood: presence.environment.mood,
    flowState: flow.flowState,
    recovery: presence.environment.pacing.recoveryCalming,
    tension: emotionalStability.tensionBalance,
  });

  const whisperLevel: InvisibleOperationalIntelligence["whisperLevel"] =
    flow.operationalSilenceWindow || calmAttention === "silent"
      ? "silent"
      : immersionActive || calmAttention === "passive"
        ? "passive"
        : "normal";

  const intelligenceWhisper = buildIntelligenceWhisper(
    flow,
    assistance,
    trustAtmosphere,
    whisperLevel,
    presence,
  );

  const intelligenceClassName = [
    presence.presenceClassName,
    `mc-flow-${flow.flowState}`,
    immersionActive ? "mc-flow-immersed mc-deep-focus-immersion" : "",
    flow.minimizeMotion ? "mc-flow-minimal-motion" : "",
    flow.operationalSilenceWindow ? "mc-operational-silence" : "",
    assistance.silentSimplification ? "mc-invisible-assistance" : "",
    trustAtmosphere.atmosphereClassName,
    emotionalStability.stabilityClassName,
    `mc-attention-${calmAttention}`,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    presence,
    flow,
    assistance,
    trustAtmosphere,
    emotionalStability,
    calmAttention,
    immersionActive,
    intelligenceWhisper,
    intelligenceClassName,
    whisperLevel,
  };
}

function buildIntelligenceWhisper(
  flow: CognitiveFlowState,
  assistance: InvisibleAssistanceState,
  trust: TrustAtmosphereState,
  whisperLevel: InvisibleOperationalIntelligence["whisperLevel"],
  presence: CognitiveOperationalPresence,
): string {
  if (whisperLevel === "silent") {
    return assistance.passiveGuidance ?? trust.atmospherePhrase;
  }
  if (flow.flowState === "immersed") {
    return assistance.passiveGuidance ?? flow.flowWhisper;
  }
  if (trust.recoveryCalmness) {
    return trust.atmospherePhrase;
  }
  return assistance.passiveGuidance ?? flow.flowWhisper ?? presence.presenceWhisper;
}
