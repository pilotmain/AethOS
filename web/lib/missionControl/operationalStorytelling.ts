/** Phase 10.1.5.2+10.1.5.4 — Operational storytelling & narrative compression. */

import type { EmotionalTrustState } from "@/lib/missionControl/emotionalTrust";
import type { HumanRealismState } from "@/lib/missionControl/humanRealism";
import type { CalmComputingState } from "@/lib/missionControl/calmComputing";
import type { CognitiveHarmonyState } from "@/lib/missionControl/cognitiveHarmony";
import type { OperationalErgonomicsState } from "@/lib/missionControl/operationalErgonomics";
import type { CognitiveErgonomicsState } from "@/lib/missionControl/cognitiveErgonomics";
import type { CognitiveSustainabilityState } from "@/lib/missionControl/cognitiveSustainability";
import type { EmotionalResilienceState } from "@/lib/missionControl/emotionalResilience";
import type { OperationalSerenityState } from "@/lib/missionControl/operationalSerenity";
import {
  buildOverviewIntelligenceFindings,
  type IntelligenceFinding,
  type StructuredFindingInput,
} from "@/lib/missionControl/intelligenceFinding";

export type OperationalNarrative = {
  primaryStory: string;
  secondaryStory: string;
  companionNote: string;
  companionHeadline: string;
  recoveryStory: string | null;
  compressedAlerts: string[];
  dominantNarrative: string | null;
  /** Evidence-first structured findings for operator-grade presentation. */
  structuredFindings: IntelligenceFinding[];
};

export type CompressionInput = {
  replayAlertCount?: number;
  telemetryAlertCount?: number;
  recommendationCount?: number;
  replayDegraded?: boolean;
};

export function compressOperationalEvents(input: CompressionInput): string[] {
  return compressOperationalEventsV6(input);
}

/** Phase 10.1.5.9 — Operational convergence with continued stability reassurance. */
export function compressOperationalEventsV6(
  input: CompressionInput & { recoveryNotices?: number; confidenceChanges?: number; confidenceWarnings?: number },
): string[] {
  const replayCount = input.replayAlertCount ?? (input.replayDegraded ? 1 : 0);
  const telemetryCount = input.telemetryAlertCount ?? 0;
  const recCount = input.recommendationCount ?? 0;
  const recoveryCount = input.recoveryNotices ?? 0;
  const confidenceChanges = input.confidenceChanges ?? 0;
  const confidenceWarnings = input.confidenceWarnings ?? 0;
  const totalSignals = replayCount + telemetryCount + recCount + recoveryCount + confidenceChanges + confidenceWarnings;
  const categories = [
    replayCount > 0,
    telemetryCount > 0,
    recCount > 0,
    recoveryCount > 0,
    confidenceChanges > 0,
    confidenceWarnings > 0,
  ].filter(Boolean).length;

  if (totalSignals >= 2 || categories >= 2 || replayCount > 0) {
    return [
      "Replay continuity instability persists across extended operational sessions, though overall operational stability continues to remain steady.",
    ];
  }

  return compressOperationalEventsV5(input);
}

/** Phase 10.1.5.8 — Operational convergence with broader stability reassurance. */
export function compressOperationalEventsV5(
  input: CompressionInput & { recoveryNotices?: number; confidenceChanges?: number; confidenceWarnings?: number },
): string[] {
  const replayCount = input.replayAlertCount ?? (input.replayDegraded ? 1 : 0);
  const telemetryCount = input.telemetryAlertCount ?? 0;
  const recCount = input.recommendationCount ?? 0;
  const recoveryCount = input.recoveryNotices ?? 0;
  const confidenceChanges = input.confidenceChanges ?? 0;
  const confidenceWarnings = input.confidenceWarnings ?? 0;
  const totalSignals = replayCount + telemetryCount + recCount + recoveryCount + confidenceChanges + confidenceWarnings;
  const categories = [
    replayCount > 0,
    telemetryCount > 0,
    recCount > 0,
    recoveryCount > 0,
    confidenceChanges > 0,
    confidenceWarnings > 0,
  ].filter(Boolean).length;

  if (totalSignals >= 2 || categories >= 2 || replayCount > 0) {
    return [
      "Replay continuity instability persists across extended operational sessions, though broader operational stability remains steady.",
    ];
  }

  return compressOperationalEventsV4(input);
}

/** Phase 10.1.5.7 — Operational convergence with steady-state reassurance. */
export function compressOperationalEventsV4(input: CompressionInput & { recoveryNotices?: number; confidenceChanges?: number }): string[] {
  const replayCount = input.replayAlertCount ?? (input.replayDegraded ? 1 : 0);
  const telemetryCount = input.telemetryAlertCount ?? 0;
  const recCount = input.recommendationCount ?? 0;
  const recoveryCount = input.recoveryNotices ?? 0;
  const confidenceChanges = input.confidenceChanges ?? 0;
  const totalSignals = replayCount + telemetryCount + recCount + recoveryCount + confidenceChanges;
  const categories = [replayCount > 0, telemetryCount > 0, recCount > 0, recoveryCount > 0, confidenceChanges > 0].filter(Boolean).length;

  if (totalSignals >= 2 || categories >= 2 || replayCount > 1) {
    return [
      "Replay continuity instability continues across extended operational sessions, though overall operational stability remains steady.",
    ];
  }

  return compressOperationalEventsV3(input);
}

/** Phase 10.1.5.6 — Multi-event convergence with stability reassurance. */
export function compressOperationalEventsV3(input: CompressionInput & { recoveryNotices?: number }): string[] {
  const replayCount = input.replayAlertCount ?? (input.replayDegraded ? 1 : 0);
  const telemetryCount = input.telemetryAlertCount ?? 0;
  const recCount = input.recommendationCount ?? 0;
  const recoveryCount = input.recoveryNotices ?? 0;
  const totalSignals = replayCount + telemetryCount + recCount + recoveryCount;
  const categories = [replayCount > 0, telemetryCount > 0, recCount > 0, recoveryCount > 0].filter(Boolean).length;

  if (totalSignals >= 3 || categories >= 2 || (replayCount > 1 && totalSignals > 1)) {
    return [
      "Replay continuity instability has persisted across extended operational sessions, though overall operational stability remains intact.",
    ];
  }

  return compressOperationalEventsV2(input);
}

/** Phase 10.1.5.5 — Event convergence — one calm narrative instead of repeated alerts. */
export function compressOperationalEventsV2(input: CompressionInput): string[] {
  const replayCount = input.replayAlertCount ?? (input.replayDegraded ? 1 : 0);
  const telemetryCount = input.telemetryAlertCount ?? 0;
  const recCount = input.recommendationCount ?? 0;
  const categories = [replayCount > 1, telemetryCount > 1, recCount > 2].filter(Boolean).length;

  if (categories >= 2 || (replayCount > 1 && (telemetryCount > 0 || recCount > 0))) {
    return [
      "Replay continuity instability has been consistently observed across long-running operational sessions.",
    ];
  }

  const compressed: string[] = [];

  if (replayCount > 1) {
    compressed.push(
      "Replay continuity instability has been consistently observed across long-running operational sessions.",
    );
  } else if (replayCount === 1) {
    compressed.push("Replay continuity instability observed across long-running operational sessions.");
  }

  if (telemetryCount > 1) {
    compressed.push(
      `Related telemetry signals (${telemetryCount} grouped) — consolidated for calmer review.`,
    );
  }

  if (recCount > 2) {
    compressed.push(
      `Operational stability recommendations (${recCount} related items grouped for clarity).`,
    );
  } else if (recCount > 0 && replayCount <= 1 && telemetryCount <= 1) {
    if (recCount === 1) {
      compressed.push("One recommendation pending — focused validation is the highest-impact next step.");
    }
  }

  return compressed;
}

export function buildOperationalNarrative(input: {
  priorityIssue: string;
  confidence: number;
  confidenceLabel: string;
  replayDegraded?: boolean;
  anomalyCount?: number;
  preflightActive?: boolean;
  recentlyResolved?: boolean;
  pendingRecommendations?: number;
  dominantThought?: string | null;
  replayDetail?: string;
  reasoning?: string;
  emotionalTrust?: EmotionalTrustState;
  humanRealism?: HumanRealismState;
  serenity?: OperationalSerenityState;
  calmComputing?: CalmComputingState;
  ergonomics?: OperationalErgonomicsState;
  harmony?: CognitiveHarmonyState;
  cognitiveErgonomics?: CognitiveErgonomicsState;
  emotionalResilience?: EmotionalResilienceState;
  cognitiveSustainability?: CognitiveSustainabilityState;
  compression?: CompressionInput & { recoveryNotices?: number; confidenceChanges?: number; confidenceWarnings?: number };
}): OperationalNarrative {
  const issue = input.priorityIssue.replace(/^the /i, "");
  const trust = input.emotionalTrust;
  const human = input.humanRealism;
  const serenity = input.serenity;
  const calm = input.calmComputing;
  const ergonomics = input.ergonomics;
  const harmony = input.harmony;
  const cognitiveErgonomics = input.cognitiveErgonomics;
  const emotionalResilience = input.emotionalResilience;
  const cognitiveSustainability = input.cognitiveSustainability;

  const primaryStory = trust
    ? `Confidence ${input.confidence.toFixed(2)} (${input.confidenceLabel}). ${trust.confidencePhrase}`
    : input.replayDegraded
      ? `Replay continuity confidence decreased after extended runtime activity (confidence ${input.confidence.toFixed(2)}). Operational stability signals remain intact; long-session replay stitching requires validation.`
      : `Operational confidence is ${input.confidenceLabel} (${input.confidence.toFixed(2)}). Current focus: ${issue}.`;

  const secondaryStory = input.recentlyResolved || input.confidence >= 0.82
    ? `Confidence recovered to ${input.confidence.toFixed(2)}. Extended-session replay validation remains recommended before broader rollout.`
    : input.preflightActive
      ? "Engineering preflights are active — governed changes await operator review before execution."
      : input.confidence >= 0.8
        ? "Operational confidence improved after runtime integrity convergence; replay stitching still needs long-session validation."
        : "Recommendations remain concise unless deeper replay analysis is requested.";

  const companionHeadline =
    cognitiveSustainability?.partnerHeadline ??
    cognitiveErgonomics?.companionPhrase ??
    ergonomics?.narrativeSteadiness ??
    human?.companionPhrase ??
    input.dominantThought ??
    `The highest-impact unresolved area right now is ${issue}.`;

  const companionNote = companionHeadline;

  const recoveryStory =
    input.recentlyResolved || (input.confidence >= 0.82 && !input.replayDegraded && !(input.anomalyCount ?? 0))
      ? emotionalResilience?.recoveryNarrative ??
        harmony?.recoveryPhrase ??
        calm?.recoveryPhrase ??
        serenity?.recoveryPhrase ??
        (trust?.reassurance
          ? `${trust.stabilityPhrase} ${trust.reassurance}`
          : "Operational stability improved after replay recovery. The environment is settling back into a calm operational rhythm.")
      : null;

  const compressedAlerts =
    input.compression != null
      ? compressOperationalEvents(input.compression)
      : buildLegacyCompressedAlerts(input);

  const structuredFindings = buildOverviewIntelligenceFindings({
    priorityIssue: input.priorityIssue,
    confidence: input.confidence,
    confidenceLabel: input.confidenceLabel,
    replayDegraded: input.replayDegraded,
    anomalyCount: input.anomalyCount,
    preflightActive: input.preflightActive,
    recentlyResolved: input.recentlyResolved,
    pendingRecommendations: input.pendingRecommendations,
    replayDetail: input.replayDetail,
    reasoning: input.reasoning,
  });

  if (structuredFindings[0] && (human?.companionPhrase || trust?.reassurance)) {
    structuredFindings[0] = {
      ...structuredFindings[0],
      companionCommentary: [human?.companionPhrase, trust?.reassurance, calm?.calmPhrase].filter(Boolean).join(" "),
    };
  }

  const dominantNarrative =
    structuredFindings[0]?.finding ??
    input.dominantThought ??
    companionHeadline;

  return {
    primaryStory,
    secondaryStory,
    companionNote,
    companionHeadline,
    recoveryStory,
    compressedAlerts,
    dominantNarrative,
    structuredFindings,
  };
}

function buildLegacyCompressedAlerts(input: {
  pendingRecommendations?: number;
  replayDegraded?: boolean;
  anomalyCount?: number;
}): string[] {
  const compressedAlerts: string[] = [];
  if ((input.pendingRecommendations ?? 0) > 1) {
    compressedAlerts.push(
      `Operational stability recommendations (${input.pendingRecommendations} related items grouped for clarity).`,
    );
  } else if ((input.pendingRecommendations ?? 0) === 1) {
    compressedAlerts.push("One recommendation pending — focused validation is the highest-impact next step.");
  }
  if (input.replayDegraded) {
    compressedAlerts.push("Replay continuity instability observed across long-running operational sessions.");
  }
  if ((input.anomalyCount ?? 0) > 1) {
    compressedAlerts.push(
      `${input.anomalyCount} related signals grouped — validating replay continuity is the highest-impact step.`,
    );
  } else if (input.anomalyCount === 1) {
    compressedAlerts.push("One operational signal needs attention — not production-critical yet.");
  }
  return compressedAlerts;
}

export function compressRecommendations(items: string[]): string {
  if (items.length === 0) return "";
  if (items.length === 1) return items[0]!;
  return `Operational stability recommendations (${items.length} related items grouped for clarity).`;
}
