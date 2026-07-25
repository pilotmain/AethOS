/** Phase 10.1.5.2 — Quiet intelligence — restraint, gating, attention budgeting. */

export type QuietIntelligenceState = {
  suppressSecondaryMetrics: boolean;
  suppressQuickLinks: boolean;
  maxVisibleChips: number;
  depthExpandAllowed: boolean;
  silenceReason: string | null;
};

export function assessQuietIntelligence(opts: {
  quietMode?: boolean;
  focusMode?: boolean;
  confidence?: number;
  loading?: boolean;
}): QuietIntelligenceState {
  const { quietMode = false, focusMode = false, confidence = 0.72, loading = false } = opts;

  if (loading) {
    return {
      suppressSecondaryMetrics: true,
      suppressQuickLinks: false,
      maxVisibleChips: 1,
      depthExpandAllowed: false,
      silenceReason: "Loading operational focus…",
    };
  }

  if (focusMode) {
    return {
      suppressSecondaryMetrics: true,
      suppressQuickLinks: true,
      maxVisibleChips: 1,
      depthExpandAllowed: true,
      silenceReason: "Focus mode — minimal surface active.",
    };
  }

  if (quietMode) {
    return {
      suppressSecondaryMetrics: true,
      suppressQuickLinks: false,
      maxVisibleChips: 2,
      depthExpandAllowed: true,
      silenceReason: "Quiet intelligence — holding non-essential detail.",
    };
  }

  const lowConfidence = confidence < 0.55;

  return {
    suppressSecondaryMetrics: lowConfidence,
    suppressQuickLinks: false,
    maxVisibleChips: lowConfidence ? 2 : 3,
    depthExpandAllowed: confidence >= 0.45,
    silenceReason: lowConfidence ? "Confidence gating — showing only high-signal guidance." : null,
  };
}

export function shouldShowDepthExpand(
  depth: number,
  quiet: QuietIntelligenceState,
  hasMoreContent: boolean,
): boolean {
  return quiet.depthExpandAllowed && hasMoreContent && depth < 3;
}
