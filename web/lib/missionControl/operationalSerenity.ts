/** Phase 10.1.5.6 — Operational serenity — emotional stabilization of operational work. */

import type { InvisibleOperationalIntelligence } from "@/lib/missionControl/cognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type OperationalSerenityState = {
  calmPacing: boolean;
  tensionReduced: boolean;
  recoveryAtmosphere: boolean;
  urgencyBalanced: boolean;
  silentInterval: boolean;
  confidencePaced: boolean;
  serenityPhrase: string;
  recoveryPhrase: string | null;
  serenityClassName: string;
};

export function assessOperationalSerenity(
  context: NavigationContext,
  intelligence: InvisibleOperationalIntelligence,
  opts: {
    recentlyResolved?: boolean;
    confidence?: number;
  } = {},
): OperationalSerenityState {
  const { recentlyResolved = false, confidence = 0.72 } = opts;
  const { flow, presence, emotionalStability, trustAtmosphere } = intelligence;

  const recoveryAtmosphere = recentlyResolved || presence.environment.pacing.recoveryCalming;
  const urgencyBalanced =
    presence.environment.pacing.suppressUrgencyStacking || emotionalStability.calmEscalation;
  const silentInterval = flow.operationalSilenceWindow || flow.flowState === "immersed";
  const tensionReduced = emotionalStability.tensionBalance < 0.45 || recoveryAtmosphere;
  const calmPacing = flow.minimizeMotion || recoveryAtmosphere || flow.flowState === "recovering";
  const confidencePaced = trustAtmosphere.confidencePacing !== "grounded" || confidence < 0.85;

  const serenityPhrase = recoveryAtmosphere
    ? "Operational stability improved after replay recovery. The environment is gradually returning to a steady state."
    : silentInterval
      ? "Operational serenity active — cognitive breathing room preserved."
      : tensionReduced
        ? "Environmental pacing calm — operational tension balanced for sustained clarity."
        : "Serene operational baseline — emotional steadiness maintained.";

  const recoveryPhrase = recoveryAtmosphere
    ? serenityPhrase
    : null;

  return {
    calmPacing,
    tensionReduced,
    recoveryAtmosphere,
    urgencyBalanced,
    silentInterval,
    confidencePaced,
    serenityPhrase,
    recoveryPhrase,
    serenityClassName: [
      "mc-operational-serenity",
      recoveryAtmosphere ? "mc-serenity-recovery" : "",
      silentInterval ? "mc-serenity-silent" : "",
      calmPacing ? "mc-serenity-calm" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
