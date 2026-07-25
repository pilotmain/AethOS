/** Phase 10.1.5.7 — Ambient cognitive flow — calm operational cognition orchestrator. */

import { assessCalmComputing, type CalmComputingState } from "@/lib/missionControl/calmComputing";
import {
  computeCognitivePartnership,
  type InvisibleCognitivePartnership,
} from "@/lib/missionControl/cognitivePartnership";
import { assessInvisibleGuidance, type InvisibleGuidanceState } from "@/lib/missionControl/invisibleGuidance";
import { assessOperationalErgonomics, type OperationalErgonomicsState } from "@/lib/missionControl/operationalErgonomics";
import {
  resolveProtectedAttention,
  type ProtectedAttentionLevel,
} from "@/lib/missionControl/spatialHierarchy";
import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type AmbientFlowState = "calm" | "sustained" | "investigating" | "immersive" | "recovering";

export type AmbientCognitiveFlowState = {
  flowState: AmbientFlowState;
  thoughtContinuity: boolean;
  focusPreservation: boolean;
  investigationImmersion: boolean;
  contextualSimplification: boolean;
  interruptionSuppressed: boolean;
  cognitiveRecoveryPacing: boolean;
  deepFocusEnvironment: boolean;
  ambientRhythmInvisible: boolean;
  flowWhisper: string;
};

export type AmbientCalmCognition = {
  partnership: InvisibleCognitivePartnership;
  ambientFlow: AmbientCognitiveFlowState;
  guidance: InvisibleGuidanceState;
  calmComputing: CalmComputingState;
  ergonomics: OperationalErgonomicsState;
  protectedAttention: ProtectedAttentionLevel;
  deepFocusEnvironment: boolean;
  cognitionWhisper: string;
  cognitionClassName: string;
  atmosphereLevel: "silent" | "atmospheric" | "whisper" | "normal";
};

export function assessAmbientCognitiveFlow(
  context: NavigationContext,
  partnership: InvisibleCognitivePartnership,
  opts: {
    focusMode?: boolean;
    quietMode?: boolean;
    recentlyResolved?: boolean;
  } = {},
): AmbientCognitiveFlowState {
  const { focusMode = false, quietMode = false, recentlyResolved = false } = opts;
  const { intelligence, partnership: partner, deepSerenityActive } = partnership;
  const { flow, presence } = intelligence;

  const investigating =
    flow.flowState === "investigating" ||
    flow.flowState === "immersed" ||
    Boolean(context.replayIntegrityDegraded);
  const immersive = deepSerenityActive || flow.flowState === "immersed" || focusMode;

  const flowState: AmbientFlowState = recentlyResolved || flow.flowState === "recovering"
    ? "recovering"
    : immersive
      ? "immersive"
      : investigating
        ? "investigating"
        : quietMode || flow.flowState === "sustained"
          ? "sustained"
          : "calm";

  const interruptionSuppressed = immersive || flow.operationalSilenceWindow || partner.compressUnrelatedSignals;
  const deepFocusEnvironment = immersive || (focusMode && investigating);

  const flowWhisper = deepFocusEnvironment
    ? "Ambient cognitive flow — immersive operational silence protecting sustained thought."
    : investigating
      ? "Operational thought continuity preserved — unrelated noise suppressed."
      : flowState === "recovering"
        ? "Cognitive recovery pacing — environmental rhythm returning to calm baseline."
        : "Ambient focus preserved — mental clarity supported without interface friction.";

  return {
    flowState,
    thoughtContinuity: partner.thoughtContinuity || flow.preserveMomentum,
    focusPreservation: partner.intentPreservation || quietMode || focusMode,
    investigationImmersion: partner.investigationAwareness || investigating,
    contextualSimplification: partner.compressUnrelatedSignals || flow.reduceEnvironmentalVariation,
    interruptionSuppressed,
    cognitiveRecoveryPacing: recentlyResolved || flowState === "recovering",
    deepFocusEnvironment,
    ambientRhythmInvisible: flow.minimizeMotion || deepFocusEnvironment,
    flowWhisper,
  };
}

export function computeAmbientCalmCognition(
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
): AmbientCalmCognition {
  const partnership = computeCognitivePartnership(context, opts);
  const ambientFlow = assessAmbientCognitiveFlow(context, partnership, opts);
  const guidance = assessInvisibleGuidance(context, partnership, ambientFlow, opts);
  const calmComputing = assessCalmComputing(context, partnership, opts);
  const ergonomics = assessOperationalErgonomics(context, partnership, opts);

  const deepFocusEnvironment = ambientFlow.deepFocusEnvironment || partnership.deepSerenityActive;

  const protectedAttention = resolveProtectedAttention({
    mood: partnership.intelligence.presence.environment.mood,
    flowState: ambientFlow.flowState,
    recovery: calmComputing.recoveryDecompression,
    tension: partnership.intelligence.emotionalStability.tensionBalance,
    deepFocus: deepFocusEnvironment,
  });

  const atmosphereLevel: AmbientCalmCognition["atmosphereLevel"] =
    protectedAttention === "silent" || calmComputing.silenceWindow
      ? "silent"
      : protectedAttention === "atmospheric" || deepFocusEnvironment
        ? "atmospheric"
        : protectedAttention === "whisper"
          ? "whisper"
          : "normal";

  const cognitionWhisper = buildCognitionWhisper(
    ambientFlow,
    guidance,
    calmComputing,
    ergonomics,
    atmosphereLevel,
    partnership,
  );

  const cognitionClassName = [
    partnership.partnershipClassName,
    `mc-ambient-flow-${ambientFlow.flowState}`,
    ambientFlow.ambientRhythmInvisible ? "mc-ambient-rhythm-invisible" : "",
    deepFocusEnvironment ? "mc-deep-focus-environment mc-atmospheric-stillness" : "",
    guidance.intelligentSilence ? "mc-invisible-guidance-silent" : "mc-invisible-guidance",
    calmComputing.computingClassName,
    ergonomics.ergonomicsClassName,
    `mc-attention-${protectedAttention}`,
  ]
    .filter(Boolean)
    .join(" ");

  return {
    partnership,
    ambientFlow,
    guidance,
    calmComputing,
    ergonomics,
    protectedAttention,
    deepFocusEnvironment,
    cognitionWhisper,
    cognitionClassName,
    atmosphereLevel,
  };
}

function buildCognitionWhisper(
  flow: AmbientCognitiveFlowState,
  guidance: InvisibleGuidanceState,
  calm: CalmComputingState,
  ergonomics: OperationalErgonomicsState,
  atmosphereLevel: AmbientCalmCognition["atmosphereLevel"],
  partnership: InvisibleCognitivePartnership,
): string {
  if (atmosphereLevel === "silent") {
    return calm.recoveryPhrase ?? flow.flowWhisper;
  }
  if (calm.recoveryDecompression && calm.recoveryPhrase) {
    return calm.recoveryPhrase;
  }
  if (ergonomics.narrativeSteadiness && guidance.passivePrioritization) {
    return ergonomics.narrativeSteadiness;
  }
  if (guidance.guidanceWhisper && atmosphereLevel !== "atmospheric") {
    return guidance.guidanceWhisper;
  }
  if (atmosphereLevel === "atmospheric" || flow.deepFocusEnvironment) {
    return flow.flowWhisper;
  }
  return calm.calmPhrase ?? partnership.partnershipWhisper;
}
