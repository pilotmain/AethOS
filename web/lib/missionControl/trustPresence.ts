/** Phase 10.1.5.6 — Trust presence — environmental trust felt, not only stated. */

import type { InvisibleOperationalIntelligence } from "@/lib/missionControl/cognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type TrustPresenceState = {
  atmosphericStability: string;
  restrainedUrgency: boolean;
  confidenceWeighted: boolean;
  recoveryTransition: boolean;
  uncertaintyTransparent: boolean;
  operationalSteadiness: string;
  presenceClassName: string;
};

export function assessTrustPresence(
  context: NavigationContext,
  intelligence: InvisibleOperationalIntelligence,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
    replayDegraded?: boolean;
  } = {},
): TrustPresenceState {
  const {
    confidence = 0.72,
    recentlyResolved = false,
    replayDegraded = context.replayIntegrityDegraded,
  } = opts;
  const { trustAtmosphere, presence, emotionalStability } = intelligence;

  const recoveryTransition = recentlyResolved || trustAtmosphere.recoveryCalmness;
  const uncertaintyTransparent = trustAtmosphere.visualHonesty || Boolean(replayDegraded);
  const restrainedUrgency = trustAtmosphere.restrainedUrgency && emotionalStability.calmEscalation;
  const confidenceWeighted = trustAtmosphere.confidencePacing === "restrained" || confidence < 0.82;

  const atmosphericStability = recoveryTransition
    ? "Atmospheric stability recovering — trust continuity through calm environmental transition."
    : uncertaintyTransparent
      ? "Atmospheric honesty — emphasis remains evidence-weighted under uncertainty."
      : "Atmospheric steadiness — psychological safety through environmental calm.";

  const operationalSteadiness =
    replayDegraded && confidence >= 0.7
      ? "Operational stability remains strong, though replay continuity is still being monitored during extended sessions."
      : presence.environment.mood === "stable"
        ? "Operational steadiness intact — the environment holds a trustworthy baseline."
        : "Operational steadiness preserved — urgency restrained to maintain credibility.";

  return {
    atmosphericStability,
    restrainedUrgency,
    confidenceWeighted,
    recoveryTransition,
    uncertaintyTransparent,
    operationalSteadiness,
    presenceClassName: [
      "mc-trust-presence",
      recoveryTransition ? "mc-trust-presence-recovery" : "",
      uncertaintyTransparent ? "mc-trust-presence-honest" : "mc-trust-presence-steady",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
