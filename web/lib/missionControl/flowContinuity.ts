/** Phase 10.1.5.9 — Operational flow continuity — preserve thinking momentum invisibly. */

import type { CalmOperationalConsciousness } from "@/lib/missionControl/operationalConsciousness";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type FlowContinuityState = {
  investigationContinuityMemory: boolean;
  narrativePersistence: boolean;
  interruptionShielding: boolean;
  contextualRestoration: boolean;
  silentFocusProtection: boolean;
  deepImmersionContinuity: boolean;
  continuityWhisper: string | null;
  maxSurfaces: number;
  suppressPeripheralSignals: boolean;
};

export function assessFlowContinuity(
  context: NavigationContext,
  ops: CalmOperationalConsciousness,
  opts: { focusMode?: boolean } = {},
): FlowContinuityState {
  const { focusMode = false } = opts;
  const { cognition, flowProtection, consciousness } = ops;
  const { ambientFlow, guidance, partnership } = cognition;

  const investigationContinuityMemory =
    flowProtection.flowContinuityMemory ||
    consciousness.awarenessContinuity ||
    partnership.partnership.contextMemoryActive;
  const narrativePersistence =
    consciousness.flowStatePreservation || ambientFlow.thoughtContinuity;
  const interruptionShielding =
    flowProtection.interruptionPrevented || ambientFlow.interruptionSuppressed || focusMode;
  const contextualRestoration =
    consciousness.consciousnessState === "restoring" || ambientFlow.cognitiveRecoveryPacing;
  const silentFocusProtection =
    interruptionShielding || flowProtection.environmentalStillness;
  const deepImmersionContinuity =
    ops.deepImmersion || consciousness.consciousnessState === "immersive";

  let maxSurfaces = flowProtection.maxSurfaces;
  if (deepImmersionContinuity) maxSurfaces = 1;
  else if (silentFocusProtection) maxSurfaces = Math.min(maxSurfaces, 2);

  const continuityWhisper = deepImmersionContinuity
    ? "Flow continuity preserved — operational narrative held without reorientation friction."
    : investigationContinuityMemory
      ? "Investigation continuity maintained — thinking momentum protected invisibly."
      : silentFocusProtection
        ? "Silent focus protection active — peripheral operational turbulence suppressed."
        : null;

  return {
    investigationContinuityMemory,
    narrativePersistence,
    interruptionShielding,
    contextualRestoration,
    silentFocusProtection,
    deepImmersionContinuity,
    continuityWhisper,
    maxSurfaces,
    suppressPeripheralSignals:
      silentFocusProtection ||
      flowProtection.hidePeripheralChrome ||
      Boolean(context.replayIntegrityDegraded && deepImmersionContinuity),
  };
}
