/** Phase 10.1.5.5 — Trust atmosphere — subconscious environmental confidence. */

import type { CognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type TrustAtmosphereState = {
  steadinessCue: string;
  confidencePacing: "restrained" | "measured" | "grounded";
  recoveryCalmness: boolean;
  visualHonesty: boolean;
  restrainedUrgency: boolean;
  atmospherePhrase: string;
  atmosphereClassName: string;
};

export function assessTrustAtmosphere(
  context: NavigationContext,
  presence: CognitiveOperationalPresence,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
    replayDegraded?: boolean;
  } = {},
): TrustAtmosphereState {
  const {
    confidence = 0.72,
    recentlyResolved = false,
    replayDegraded = context.replayIntegrityDegraded,
  } = opts;
  const { environment, spatialTrust } = presence;

  const recoveryCalmness = recentlyResolved || environment.pacing.recoveryCalming;
  const uncertain = replayDegraded || confidence < 0.78 || context.hasAnomalies;
  const visualHonesty = uncertain || environment.mood === "elevated";
  const restrainedUrgency = environment.mood === "critical" || environment.mood === "elevated";

  const confidencePacing: TrustAtmosphereState["confidencePacing"] =
    recoveryCalmness && confidence >= 0.82
      ? "grounded"
      : uncertain
        ? "restrained"
        : "measured";

  const atmospherePhrase = buildAtmospherePhrase({
    recoveryCalmness,
    replayDegraded: Boolean(replayDegraded),
    confidence,
    hasAnomalies: Boolean(context.hasAnomalies),
    mood: environment.mood,
  });

  const steadinessCue = recoveryCalmness
    ? "Environmental steadiness recovering — trust continuity preserved through calm transition."
    : visualHonesty
      ? "Visual honesty active — emphasis remains evidence-weighted and restrained."
      : spatialTrust.stabilityCue;

  return {
    steadinessCue,
    confidencePacing,
    recoveryCalmness,
    visualHonesty,
    restrainedUrgency,
    atmospherePhrase,
    atmosphereClassName: [
      "mc-trust-atmosphere",
      recoveryCalmness ? "mc-trust-recovery-calm" : "",
      visualHonesty ? "mc-trust-honest" : "mc-trust-steady",
    ]
      .filter(Boolean)
      .join(" "),
  };
}

function buildAtmospherePhrase(input: {
  recoveryCalmness: boolean;
  replayDegraded: boolean;
  confidence: number;
  hasAnomalies: boolean;
  mood: string;
}): string {
  if (input.recoveryCalmness) {
    return "Operational confidence improved after reliability convergence, though replay stitching still deserves extended-session validation before broader rollout.";
  }
  if (input.replayDegraded && input.confidence >= 0.72) {
    return "Operational stability remains strong, though replay continuity is still being monitored during extended sessions.";
  }
  if (input.hasAnomalies && input.mood !== "critical") {
    return "Operational stability remains intact — localized signals are being monitored with restrained emphasis.";
  }
  if (input.confidence >= 0.82 && !input.replayDegraded) {
    return "Operational stability remains strong — the environment is holding a trustworthy baseline.";
  }
  return "Trust atmosphere steady — confidence paced to evidence, not overstatement.";
}
