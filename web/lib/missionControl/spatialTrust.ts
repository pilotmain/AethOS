/** Phase 10.1.5.4 — Spatial trust signals — subconscious environmental confidence. */

import type { OperationalEnvironment } from "@/lib/missionControl/environmentalIntelligence";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type SpatialTrustState = {
  stabilityCue: string;
  recoveryTransition: boolean;
  confidenceEmphasis: "restrained" | "balanced" | "grounded";
  trustWhisper: string;
  visualRestraint: boolean;
  trustClassName: string;
};

export function assessSpatialTrust(
  context: NavigationContext,
  environment: OperationalEnvironment,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
  } = {},
): SpatialTrustState {
  const { confidence = 0.72, recentlyResolved = false } = opts;

  const recoveryTransition = recentlyResolved || environment.pacing.recoveryCalming;
  const uncertain = context.replayIntegrityDegraded || confidence < 0.72;
  const visualRestraint = uncertain || environment.mood === "elevated" || environment.mood === "critical";

  const confidenceEmphasis: SpatialTrustState["confidenceEmphasis"] =
    confidence >= 0.82 && !uncertain ? "grounded" : uncertain ? "restrained" : "balanced";

  const stabilityCue = recoveryTransition
    ? "Environmental stability recovering — transitions remain calm and gradual."
    : environment.mood === "stable"
      ? "Spatial continuity stable — environment holding a trustworthy baseline."
      : environment.mood === "critical"
        ? "Honest uncertainty — emphasis restrained to what evidence supports."
        : "Trust continuity maintained — emphasis calibrated to operational evidence.";

  const trustWhisper = recoveryTransition
    ? "Operational stability improved after recovery. The environment is settling with calm reassurance."
    : visualRestraint
      ? "Spatial trust preserved — confidence weighted to evidence, not overstatement."
      : "A calm operational companion space — trustworthy, breathable, and steady.";

  const trustClassName = [
    recoveryTransition ? "mc-trust-recovery" : "",
    visualRestraint ? "mc-trust-restrained" : "mc-trust-grounded",
  ]
    .filter(Boolean)
    .join(" ");

  return {
    stabilityCue,
    recoveryTransition,
    confidenceEmphasis,
    trustWhisper,
    visualRestraint,
    trustClassName,
  };
}
