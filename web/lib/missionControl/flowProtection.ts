/** Phase 10.1.5.8 — Invisible flow protection — friction removed before it is felt. */

import type { AmbientCalmCognition } from "@/lib/missionControl/ambientCognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type FlowProtectionState = {
  interruptionPrevented: boolean;
  noiseShielded: boolean;
  recommendationsSuppressed: boolean;
  environmentalStillness: boolean;
  contextualSimplification: boolean;
  flowContinuityMemory: boolean;
  protectionWhisper: string | null;
  maxSurfaces: number;
  hidePeripheralChrome: boolean;
};

export function assessFlowProtection(
  context: NavigationContext,
  cognition: AmbientCalmCognition,
  opts: { focusMode?: boolean } = {},
): FlowProtectionState {
  const { focusMode = false } = opts;
  const { ambientFlow, guidance, partnership } = cognition;

  const interruptionPrevented =
    ambientFlow.interruptionSuppressed || ambientFlow.deepFocusEnvironment || focusMode;
  const noiseShielded =
    partnership.partnership.compressUnrelatedSignals || ambientFlow.contextualSimplification;
  const recommendationsSuppressed =
    guidance.recommendationMinimized || partnership.partnership.attentionPressureBalanced;
  const environmentalStillness = ambientFlow.ambientRhythmInvisible || cognition.deepFocusEnvironment;
  const contextualSimplification = noiseShielded || guidance.passivePrioritization;
  const flowContinuityMemory =
    ambientFlow.thoughtContinuity || partnership.partnership.contextMemoryActive;

  let maxSurfaces = guidance.maxSurfaces;
  if (cognition.deepFocusEnvironment) maxSurfaces = 1;
  else if (interruptionPrevented) maxSurfaces = Math.min(maxSurfaces, 2);

  const protectionWhisper = interruptionPrevented
    ? "Flow protection active — peripheral noise shielded, investigation continuity preserved."
    : flowContinuityMemory
      ? "Operational flow continuity maintained — reorientation friction reduced."
      : null;

  return {
    interruptionPrevented,
    noiseShielded,
    recommendationsSuppressed,
    environmentalStillness,
    contextualSimplification,
    flowContinuityMemory,
    protectionWhisper,
    maxSurfaces,
    hidePeripheralChrome: interruptionPrevented || environmentalStillness,
  };
}
