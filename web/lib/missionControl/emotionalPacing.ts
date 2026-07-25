/** Phase 10.1.5.3 — Emotional operational pacing — calm tension modulation. */

import type { NavigationContext } from "@/lib/missionControl/sidebarNavigation";

export type EmotionalPacingState = {
  tension: number;
  escalation: "none" | "gradual" | "focused" | "critical";
  recoveryCalming: boolean;
  focusPreservation: boolean;
  pacingNote: string;
  suppressUrgencyStacking: boolean;
};

export function assessEmotionalPacing(
  context: NavigationContext,
  opts: {
    confidence?: number;
    quietMode?: boolean;
    focusMode?: boolean;
    recentlyResolved?: boolean;
  } = {},
): EmotionalPacingState {
  const { confidence = 0.72, quietMode = false, focusMode = false, recentlyResolved = false } = opts;

  if (recentlyResolved || (confidence >= 0.82 && !context.hasAnomalies && !context.replayIntegrityDegraded)) {
    return {
      tension: 0.12,
      escalation: "none",
      recoveryCalming: recentlyResolved || confidence >= 0.85,
      focusPreservation: true,
      pacingNote: "Quiet confidence — environment holding steady after stabilization.",
      suppressUrgencyStacking: true,
    };
  }

  let tension = 0.2;
  if (context.replayIntegrityDegraded) tension += 0.22;
  if (context.hasAnomalies) tension += 0.28;
  if (context.hasActivePreflights) tension += 0.12;
  if (context.hasActiveJobs) tension += 0.08;
  if (confidence < 0.55) tension += 0.15;
  tension = Math.min(0.92, tension);

  if (quietMode || focusMode) {
    tension = Math.min(tension, 0.45);
  }

  let escalation: EmotionalPacingState["escalation"] = "none";
  if (tension >= 0.75) escalation = "critical";
  else if (tension >= 0.5) escalation = "focused";
  else if (tension >= 0.28) escalation = "gradual";

  const pacingNote =
    escalation === "critical"
      ? "Progressive escalation — one singular focus, not stacked alarms."
      : escalation === "focused"
        ? "Focused validation recommended — pacing remains calm."
        : escalation === "gradual"
          ? "Gradual awareness — no urgency stacking."
          : "Emotional load balanced — operational calm maintained.";

  return {
    tension,
    escalation,
    recoveryCalming: false,
    focusPreservation: focusMode || quietMode,
    pacingNote,
    suppressUrgencyStacking: tension < 0.65,
  };
}
