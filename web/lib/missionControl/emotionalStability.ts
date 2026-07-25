/** Phase 10.1.5.5 — Emotional stability — human-centered operational ergonomics. */

import type { CognitiveOperationalPresence } from "@/lib/missionControl/cognitivePresence";
import type { CognitiveFlowState } from "@/lib/missionControl/cognitiveFlow";
import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type EmotionalStabilityState = {
  calmEscalation: boolean;
  recoveryDecompression: boolean;
  cognitiveReassurance: string | null;
  fatigueAwarePacing: boolean;
  tensionBalance: number;
  supportivePhrase: string | null;
  stabilityClassName: string;
};

export function assessEmotionalStability(
  context: NavigationContext,
  presence: CognitiveOperationalPresence,
  flow: CognitiveFlowState,
  opts: {
    confidence?: number;
    recentlyResolved?: boolean;
  } = {},
): EmotionalStabilityState {
  const { confidence = 0.72, recentlyResolved = false } = opts;
  const { environment, cognitive, emotionalTrust } = presence;

  let tensionBalance = environment.pacing.tension;
  if (flow.flowState === "immersed") tensionBalance = Math.min(tensionBalance, 0.35);
  if (flow.flowState === "recovering") tensionBalance = Math.min(tensionBalance, 0.22);
  if (recentlyResolved) tensionBalance = Math.min(tensionBalance, 0.18);

  const calmEscalation = environment.mood === "critical" && tensionBalance < 0.85;
  const recoveryDecompression = flow.flowState === "recovering" || environment.pacing.recoveryCalming;
  const fatigueAwarePacing = cognitive.fatigueSensed || flow.interruptionCost >= 0.4;

  const cognitiveReassurance =
    recoveryDecompression
      ? "Recovery decompression active — emotional load easing after stabilization."
      : fatigueAwarePacing
        ? "Fatigue-aware pacing — the environment is reducing stimulation to sustain clarity."
        : emotionalTrust.reassurance;

  const supportivePhrase =
    context.replayIntegrityDegraded && !recoveryDecompression
      ? "Operational empathy active — replay validation is framed as prudent follow-up, not alarm."
      : recoveryDecompression
        ? "Grounded steadiness — confidence improving without overstating certainty."
        : null;

  return {
    calmEscalation,
    recoveryDecompression,
    cognitiveReassurance,
    fatigueAwarePacing,
    tensionBalance,
    supportivePhrase,
    stabilityClassName: [
      "mc-emotional-steady",
      recoveryDecompression ? "mc-emotional-recovery" : "",
      fatigueAwarePacing ? "mc-emotional-fatigue-aware" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}
