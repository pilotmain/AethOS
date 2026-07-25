/** Phase 10.1.5.6 — Cognitive partnership — invisible operational companion. */

import {
  computeInvisibleOperationalIntelligence,
  type InvisibleOperationalIntelligence,
} from "@/lib/missionControl/cognitiveFlow";
import { assessHumanRealism, type HumanRealismState } from "@/lib/missionControl/humanRealism";
import { assessOperationalSerenity, type OperationalSerenityState } from "@/lib/missionControl/operationalSerenity";
import { assessTrustPresence, type TrustPresenceState } from "@/lib/missionControl/trustPresence";
import {
  resolveCognitiveAttention,
  type CognitiveAttentionLevel,
} from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type CognitivePartnershipState = {
  thoughtContinuity: boolean;
  investigationAwareness: boolean;
  silentAssistance: boolean;
  intentPreservation: boolean;
  attentionPressureBalanced: boolean;
  contextMemoryActive: boolean;
  partnershipWhisper: string;
  companionHeadline: string | null;
  minimizeInteractionFriction: boolean;
  compressUnrelatedSignals: boolean;
};

export type InvisibleCognitivePartnership = {
  intelligence: InvisibleOperationalIntelligence;
  partnership: CognitivePartnershipState;
  serenity: OperationalSerenityState;
  trustPresence: TrustPresenceState;
  humanRealism: HumanRealismState;
  cognitiveAttention: CognitiveAttentionLevel;
  deepSerenityActive: boolean;
  partnershipWhisper: string;
  partnershipClassName: string;
  whisperLevel: "silent" | "whisper" | "ambient" | "normal";
};

export function assessCognitivePartnership(
  context: NavigationContext,
  intelligence: InvisibleOperationalIntelligence,
  opts: {
    priorityIssue?: string;
    recentlyResolved?: boolean;
    focusMode?: boolean;
  } = {},
): CognitivePartnershipState {
  const { priorityIssue, recentlyResolved = false, focusMode = false } = opts;
  const { flow, assistance, presence } = intelligence;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "operational validation";

  const investigating = flow.flowState === "investigating" || flow.flowState === "immersed";
  const thoughtContinuity = investigating || flow.preserveMomentum || focusMode;
  const investigationAwareness = context.replayIntegrityDegraded || investigating;
  const silentAssistance = assistance.backgroundIntelligence || flow.operationalSilenceWindow;
  const intentPreservation = thoughtContinuity && !recentlyResolved;
  const attentionPressureBalanced =
    presence.invisible.suppressWeakRecommendations || flow.pauseWeakRecommendations;
  const contextMemoryActive = investigationAwareness || presence.cognitive.focusContinuity;

  const companionHeadline = investigationAwareness
    ? `The highest-impact unresolved area right now is ${issue}.`
    : null;

  const partnershipWhisper = silentAssistance
    ? "Cognitive partnership active — investigation context preserved, unrelated signals compressed."
    : thoughtContinuity
      ? "Operational thought continuity maintained — smoother reorientation across the session."
      : "Invisible companion support — calm assistance without interruption.";

  return {
    thoughtContinuity,
    investigationAwareness,
    silentAssistance,
    intentPreservation,
    attentionPressureBalanced,
    contextMemoryActive,
    partnershipWhisper,
    companionHeadline,
    minimizeInteractionFriction: flow.flowState === "immersed" || focusMode,
    compressUnrelatedSignals: flow.suppressSecondaryDomains || assistance.silentSimplification,
  };
}

export function computeCognitivePartnership(
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
): InvisibleCognitivePartnership {
  const intelligence = computeInvisibleOperationalIntelligence(context, opts);
  const partnership = assessCognitivePartnership(context, intelligence, opts);
  const serenity = assessOperationalSerenity(context, intelligence, opts);
  const trustPresence = assessTrustPresence(context, intelligence, opts);
  const humanRealism = assessHumanRealism(context, intelligence, opts);

  const deepSerenityActive =
    serenity.silentInterval ||
    intelligence.immersionActive ||
    intelligence.flow.flowState === "immersed";

  const cognitiveAttention = resolveCognitiveAttention({
    mood: intelligence.presence.environment.mood,
    flowState: intelligence.flow.flowState,
    recovery: serenity.recoveryAtmosphere,
    tension: intelligence.emotionalStability.tensionBalance,
    deepSerenity: deepSerenityActive,
  });

  const whisperLevel: InvisibleCognitivePartnership["whisperLevel"] =
    cognitiveAttention === "silent" || serenity.silentInterval
      ? "silent"
      : cognitiveAttention === "whisper" || deepSerenityActive
        ? "whisper"
        : intelligence.whisperLevel === "passive"
          ? "ambient"
          : "normal";

  const partnershipWhisper = buildPartnershipWhisper(
    partnership,
    serenity,
    trustPresence,
    humanRealism,
    whisperLevel,
    intelligence,
  );

  const partnershipClassName = [
    intelligence.intelligenceClassName,
    partnership.thoughtContinuity ? "mc-partnership-continuity" : "",
    deepSerenityActive ? "mc-deep-serenity mc-serenity-immersed" : "",
    serenity.serenityClassName,
    trustPresence.presenceClassName,
    humanRealism.emotionalSteadiness ? "mc-human-steady" : "",
    `mc-attention-${cognitiveAttention}`,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    intelligence,
    partnership,
    serenity,
    trustPresence,
    humanRealism,
    cognitiveAttention,
    deepSerenityActive,
    partnershipWhisper,
    partnershipClassName,
    whisperLevel,
  };
}

function buildPartnershipWhisper(
  partnership: CognitivePartnershipState,
  serenity: OperationalSerenityState,
  trust: TrustPresenceState,
  human: HumanRealismState,
  whisperLevel: InvisibleCognitivePartnership["whisperLevel"],
  intelligence: InvisibleOperationalIntelligence,
): string {
  if (whisperLevel === "silent") {
    return serenity.recoveryPhrase ?? partnership.partnershipWhisper;
  }
  if (serenity.recoveryAtmosphere) {
    return serenity.serenityPhrase;
  }
  if (human.companionPhrase && partnership.investigationAwareness) {
    return human.companionPhrase;
  }
  if (whisperLevel === "whisper") {
    return partnership.partnershipWhisper;
  }
  return trust.operationalSteadiness ?? intelligence.intelligenceWhisper;
}
