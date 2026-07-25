/** Phase 10.1.5.8 — Operational consciousness — calm cognitive field orchestrator. */

import {
  computeAmbientCalmCognition,
  type AmbientCalmCognition,
} from "@/lib/missionControl/ambientCognitiveFlow";
import { assessCognitiveErgonomics, type CognitiveErgonomicsState } from "@/lib/missionControl/cognitiveErgonomics";
import { assessCognitiveHarmony, type CognitiveHarmonyState } from "@/lib/missionControl/cognitiveHarmony";
import { assessFlowProtection, type FlowProtectionState } from "@/lib/missionControl/flowProtection";
import {
  resolveHarmoniousAttention,
  type HarmoniousAttentionLevel,
} from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type ConsciousnessState = "resting" | "aware" | "focused" | "immersive" | "restoring";

export type OperationalConsciousnessField = {
  consciousnessState: ConsciousnessState;
  awarenessContinuity: boolean;
  cognitiveProtection: boolean;
  immersionPreservation: boolean;
  focusStabilization: boolean;
  adaptiveQuieting: boolean;
  flowStatePreservation: boolean;
  consciousnessWhisper: string;
  companionHeadline: string | null;
};

export type CalmOperationalConsciousness = {
  cognition: AmbientCalmCognition;
  consciousness: OperationalConsciousnessField;
  flowProtection: FlowProtectionState;
  harmony: CognitiveHarmonyState;
  cognitiveErgonomics: CognitiveErgonomicsState;
  harmoniousAttention: HarmoniousAttentionLevel;
  deepImmersion: boolean;
  consciousnessWhisper: string;
  consciousnessClassName: string;
  atmosphereLevel: "invisible" | "atmospheric" | "whisper" | "normal";
};

export function assessOperationalConsciousness(
  context: NavigationContext,
  cognition: AmbientCalmCognition,
  opts: {
    priorityIssue?: string;
    focusMode?: boolean;
    recentlyResolved?: boolean;
  } = {},
): OperationalConsciousnessField {
  const { priorityIssue, focusMode = false, recentlyResolved = false } = opts;
  const issue = priorityIssue?.replace(/^the /i, "") ?? "operational validation";
  const { ambientFlow, partnership } = cognition;

  const consciousnessState: ConsciousnessState = recentlyResolved || ambientFlow.flowState === "recovering"
    ? "restoring"
    : cognition.deepFocusEnvironment || ambientFlow.flowState === "immersive"
      ? "immersive"
      : ambientFlow.investigationImmersion
        ? "focused"
        : ambientFlow.flowState === "sustained"
          ? "aware"
          : "resting";

  const awarenessContinuity = ambientFlow.thoughtContinuity || partnership.partnership.thoughtContinuity;
  const cognitiveProtection = ambientFlow.interruptionSuppressed || cognition.deepFocusEnvironment;
  const immersionPreservation = ambientFlow.investigationImmersion || focusMode;
  const focusStabilization = immersionPreservation || ambientFlow.focusPreservation;
  const adaptiveQuieting = ambientFlow.contextualSimplification || ambientFlow.ambientRhythmInvisible;
  const flowStatePreservation = awarenessContinuity && !recentlyResolved;

  const companionHeadline = immersionPreservation
    ? `The highest-impact unresolved area right now is ${issue}.`
    : null;

  const consciousnessWhisper = cognitiveProtection
    ? "Operational consciousness active — cognitive field protecting focus and environmental steadiness."
    : awarenessContinuity
      ? "Awareness continuity preserved — investigation context held without peripheral noise."
      : "Calm operational consciousness — mental clarity supported invisibly.";

  return {
    consciousnessState,
    awarenessContinuity,
    cognitiveProtection,
    immersionPreservation,
    focusStabilization,
    adaptiveQuieting,
    flowStatePreservation,
    consciousnessWhisper,
    companionHeadline,
  };
}

export function computeOperationalConsciousness(
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
): CalmOperationalConsciousness {
  const cognition = computeAmbientCalmCognition(context, opts);
  const consciousness = assessOperationalConsciousness(context, cognition, opts);
  const flowProtection = assessFlowProtection(context, cognition, opts);
  const harmony = assessCognitiveHarmony(context, cognition, opts);
  const cognitiveErgonomics = assessCognitiveErgonomics(context, cognition, opts);

  const deepImmersion = cognition.deepFocusEnvironment || flowProtection.environmentalStillness;

  const harmoniousAttention = resolveHarmoniousAttention({
    mood: cognition.partnership.intelligence.presence.environment.mood,
    consciousnessState: consciousness.consciousnessState,
    recovery: harmony.recoveryAtmosphere,
    tension: cognition.partnership.intelligence.emotionalStability.tensionBalance,
    deepImmersion,
  });

  const atmosphereLevel: CalmOperationalConsciousness["atmosphereLevel"] =
    harmoniousAttention === "invisible" || flowProtection.hidePeripheralChrome
      ? "invisible"
      : harmoniousAttention === "atmospheric" || deepImmersion
        ? "atmospheric"
        : harmoniousAttention === "whisper"
          ? "whisper"
          : "normal";

  const consciousnessWhisper = buildConsciousnessWhisper(
    consciousness,
    flowProtection,
    harmony,
    cognitiveErgonomics,
    atmosphereLevel,
    cognition,
  );

  const consciousnessClassName = [
    cognition.cognitionClassName,
    `mc-consciousness-${consciousness.consciousnessState}`,
    consciousness.adaptiveQuieting ? "mc-consciousness-quiet" : "",
    deepImmersion ? "mc-deep-cognitive-immersion mc-immersive-silence" : "",
    flowProtection.environmentalStillness ? "mc-flow-protected" : "",
    harmony.harmonyClassName,
    cognitiveErgonomics.ergonomicsClassName,
    `mc-attention-${harmoniousAttention}`,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    cognition,
    consciousness,
    flowProtection,
    harmony,
    cognitiveErgonomics,
    harmoniousAttention,
    deepImmersion,
    consciousnessWhisper,
    consciousnessClassName,
    atmosphereLevel,
  };
}

function buildConsciousnessWhisper(
  field: OperationalConsciousnessField,
  protection: FlowProtectionState,
  harmony: CognitiveHarmonyState,
  ergonomics: CognitiveErgonomicsState,
  atmosphereLevel: CalmOperationalConsciousness["atmosphereLevel"],
  cognition: AmbientCalmCognition,
): string {
  if (atmosphereLevel === "invisible") {
    return harmony.recoveryPhrase ?? protection.protectionWhisper ?? field.consciousnessWhisper;
  }
  if (harmony.recoveryAtmosphere && harmony.recoveryPhrase) {
    return harmony.recoveryPhrase;
  }
  if (ergonomics.companionPhrase && field.immersionPreservation) {
    return ergonomics.companionPhrase;
  }
  if (protection.protectionWhisper && atmosphereLevel === "whisper") {
    return protection.protectionWhisper;
  }
  if (atmosphereLevel === "atmospheric" || cognition.deepFocusEnvironment) {
    return field.consciousnessWhisper;
  }
  return harmony.harmonyPhrase ?? cognition.cognitionWhisper;
}
