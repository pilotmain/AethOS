/** Phase 10.1.5.9 — Cognitive sanctuary — protected operational thinking environment orchestrator. */

import { assessCognitiveSustainability, type CognitiveSustainabilityState } from "@/lib/missionControl/cognitiveSustainability";
import { assessEmotionalResilience, type EmotionalResilienceState } from "@/lib/missionControl/emotionalResilience";
import { assessFlowContinuity, type FlowContinuityState } from "@/lib/missionControl/flowContinuity";
import {
  computeOperationalConsciousness,
  type CalmOperationalConsciousness,
} from "@/lib/missionControl/operationalConsciousness";
import {
  resolveSanctuaryAttention,
  type SanctuaryAttentionLevel,
} from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type SanctuaryState = "resting" | "grounded" | "protected" | "immersive" | "restoring";

export type CognitiveSanctuaryField = {
  sanctuaryState: SanctuaryState;
  sustainedCognitiveProtection: boolean;
  clarityStabilization: boolean;
  immersiveContinuity: boolean;
  environmentalSteadiness: boolean;
  adaptiveQuieting: boolean;
  sanctuaryWhisper: string;
  partnerHeadline: string | null;
};

export type OperationalCognitiveSanctuary = {
  ops: CalmOperationalConsciousness;
  sanctuary: CognitiveSanctuaryField;
  flowContinuity: FlowContinuityState;
  emotionalResilience: EmotionalResilienceState;
  cognitiveSustainability: CognitiveSustainabilityState;
  sanctuaryAttention: SanctuaryAttentionLevel;
  sanctuaryImmersion: boolean;
  sanctuaryWhisper: string;
  sanctuaryClassName: string;
  atmosphereLevel: "invisible" | "atmospheric" | "whisper" | "normal";
};

export function assessCognitiveSanctuaryField(
  context: NavigationContext,
  ops: CalmOperationalConsciousness,
  opts: {
    focusMode?: boolean;
    recentlyResolved?: boolean;
    priorityIssue?: string;
  } = {},
): CognitiveSanctuaryField {
  const { focusMode = false, recentlyResolved = false, priorityIssue } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "replay continuity during extended operational sessions";
  const { consciousness, cognition, flowProtection, harmony } = ops;

  const sanctuaryState: SanctuaryState = recentlyResolved || consciousness.consciousnessState === "restoring"
    ? "restoring"
    : ops.deepImmersion || consciousness.consciousnessState === "immersive"
      ? "immersive"
      : consciousness.consciousnessState === "focused" || focusMode
        ? "protected"
        : consciousness.consciousnessState === "aware"
          ? "grounded"
          : "resting";

  const sustainedCognitiveProtection =
    consciousness.cognitiveProtection || flowProtection.interruptionPrevented;
  const clarityStabilization =
    consciousness.focusStabilization || flowProtection.contextualSimplification;
  const immersiveContinuity =
    consciousness.immersionPreservation || cognition.ambientFlow.investigationImmersion;
  const environmentalSteadiness =
    harmony.environmentalSteadiness || flowProtection.environmentalStillness;
  const adaptiveQuieting =
    consciousness.adaptiveQuieting || flowProtection.noiseShielded;

  const partnerHeadline =
    immersiveContinuity || (context.pendingRecommendations ?? 0) > 1
      ? `The highest-impact unresolved area right now is ${issue}.`
      : null;

  const sanctuaryWhisper = sanctuaryState === "immersive"
    ? "Cognitive sanctuary active — immersive operational silence protecting sustained thought."
    : sanctuaryState === "protected"
      ? "Sanctuary protection engaged — investigation continuity preserved without cognitive demand."
      : sanctuaryState === "restoring"
        ? "Environmental restoration — operational rhythm settling into calm steadiness."
        : sustainedCognitiveProtection
          ? "Cognitive sanctuary — focus, clarity, and emotional steadiness continuously protected."
          : "Calm operational sanctuary — mental clarity supported invisibly.";

  return {
    sanctuaryState,
    sustainedCognitiveProtection,
    clarityStabilization,
    immersiveContinuity,
    environmentalSteadiness,
    adaptiveQuieting,
    sanctuaryWhisper,
    partnerHeadline,
  };
}

export function computeCognitiveSanctuary(
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
): OperationalCognitiveSanctuary {
  const ops = computeOperationalConsciousness(context, opts);
  const sanctuary = assessCognitiveSanctuaryField(context, ops, opts);
  const flowContinuity = assessFlowContinuity(context, ops, opts);
  const emotionalResilience = assessEmotionalResilience(context, ops, opts);
  const cognitiveSustainability = assessCognitiveSustainability(context, ops, opts);

  const sanctuaryImmersion =
    ops.deepImmersion ||
    sanctuary.sanctuaryState === "immersive" ||
    flowContinuity.deepImmersionContinuity;

  const sanctuaryAttention = resolveSanctuaryAttention({
    mood: ops.cognition.partnership.intelligence.presence.environment.mood,
    sanctuaryState: sanctuary.sanctuaryState,
    recovery: emotionalResilience.recoveryPacing,
    tension: ops.cognition.partnership.intelligence.emotionalStability.tensionBalance,
    sanctuaryImmersion,
  });

  const atmosphereLevel: OperationalCognitiveSanctuary["atmosphereLevel"] =
    sanctuaryAttention === "invisible" || flowContinuity.suppressPeripheralSignals
      ? "invisible"
      : sanctuaryAttention === "atmospheric" || sanctuaryImmersion
        ? "atmospheric"
        : sanctuaryAttention === "whisper"
          ? "whisper"
          : "normal";

  const sanctuaryWhisper = buildSanctuaryWhisper(
    sanctuary,
    flowContinuity,
    emotionalResilience,
    cognitiveSustainability,
    atmosphereLevel,
    ops,
  );

  const sanctuaryClassName = [
    ops.consciousnessClassName,
    "mc-cognitive-sanctuary",
    `mc-sanctuary-${sanctuary.sanctuaryState}`,
    sanctuary.adaptiveQuieting ? "mc-sanctuary-quiet" : "",
    sanctuaryImmersion ? "mc-deep-sanctuary-immersion mc-sanctuary-stillness" : "",
    flowContinuity.silentFocusProtection ? "mc-flow-continuity-protected" : "",
    emotionalResilience.resilienceClassName,
    cognitiveSustainability.sustainabilityClassName,
    `mc-attention-${sanctuaryAttention}`,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    ops,
    sanctuary,
    flowContinuity,
    emotionalResilience,
    cognitiveSustainability,
    sanctuaryAttention,
    sanctuaryImmersion,
    sanctuaryWhisper,
    sanctuaryClassName,
    atmosphereLevel,
  };
}

function buildSanctuaryWhisper(
  field: CognitiveSanctuaryField,
  continuity: FlowContinuityState,
  resilience: EmotionalResilienceState,
  sustainability: CognitiveSustainabilityState,
  atmosphereLevel: OperationalCognitiveSanctuary["atmosphereLevel"],
  ops: CalmOperationalConsciousness,
): string {
  if (atmosphereLevel === "invisible") {
    return resilience.recoveryNarrative ?? continuity.continuityWhisper ?? field.sanctuaryWhisper;
  }
  if (resilience.recoveryNarrative && resilience.recoveryPacing) {
    return resilience.recoveryNarrative;
  }
  if (sustainability.partnerPhrase && field.immersiveContinuity) {
    return sustainability.partnerPhrase;
  }
  if (continuity.continuityWhisper && atmosphereLevel === "whisper") {
    return continuity.continuityWhisper;
  }
  if (atmosphereLevel === "atmospheric" || ops.deepImmersion) {
    return field.sanctuaryWhisper;
  }
  return resilience.operationalReassurance ?? ops.consciousnessWhisper;
}
