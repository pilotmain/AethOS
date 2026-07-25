import { describe, expect, it } from "vitest";

import {
  assessCognitivePartnership,
  computeCognitivePartnership,
} from "@/lib/missionControl/cognitivePartnership";
import { computeInvisibleOperationalIntelligence } from "@/lib/missionControl/cognitiveFlow";
import { assessHumanRealism } from "@/lib/missionControl/humanRealism";
import { assessOperationalSerenity } from "@/lib/missionControl/operationalSerenity";
import {
  buildOperationalNarrative,
  compressOperationalEventsV4,
} from "@/lib/missionControl/operationalStorytelling";
import { resolveCognitiveAttention } from "@/lib/missionControl/spatialHierarchy";
import { assessTrustPresence } from "@/lib/missionControl/trustPresence";

describe("cognitivePartnership", () => {
  it("preserves investigation context during extended debugging", () => {
    const partnership = computeCognitivePartnership(
      { replayIntegrityDegraded: true, hasActiveJobs: true, pendingRecommendations: 4 },
      { focusMode: true, priorityIssue: "replay continuity validation" },
    );
    expect(partnership.partnership.thoughtContinuity).toBe(true);
    expect(partnership.partnership.compressUnrelatedSignals).toBe(true);
    expect(partnership.partnership.minimizeInteractionFriction).toBe(true);
    expect(partnership.deepSerenityActive).toBe(true);
  });

  it("provides companion headline for unresolved recommendations", () => {
    const partnership = computeCognitivePartnership(
      { replayIntegrityDegraded: true, pendingRecommendations: 4 },
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    expect(partnership.partnership.companionHeadline).toContain("highest-impact unresolved area");
  });

  it("assesses partnership support from intelligence stack", () => {
    const intelligence = computeInvisibleOperationalIntelligence({ replayIntegrityDegraded: true });
    const partner = assessCognitivePartnership({ replayIntegrityDegraded: true }, intelligence, {
      priorityIssue: "replay continuity",
    });
    expect(partner.investigationAwareness).toBe(true);
    expect(partner.silentAssistance).toBe(true);
  });
});

describe("operationalSerenity", () => {
  it("signals recovery serenity after stabilization", () => {
    const intelligence = computeInvisibleOperationalIntelligence({}, { recentlyResolved: true, confidence: 0.88 });
    const serenity = assessOperationalSerenity({}, intelligence, { recentlyResolved: true, confidence: 0.88 });
    expect(serenity.recoveryAtmosphere).toBe(true);
    expect(serenity.serenityPhrase).toContain("gradually returning to a steady state");
    expect(serenity.recoveryPhrase).toContain("replay recovery");
  });

  it("activates silent intervals during immersion", () => {
    const partnership = computeCognitivePartnership({ replayIntegrityDegraded: true }, { focusMode: true });
    expect(partnership.serenity.silentInterval).toBe(true);
    expect(partnership.serenity.calmPacing).toBe(true);
  });
});

describe("trustPresence", () => {
  it("communicates environmental steadiness under replay monitoring", () => {
    const intelligence = computeInvisibleOperationalIntelligence({ replayIntegrityDegraded: true }, { confidence: 0.8 });
    const trust = assessTrustPresence({ replayIntegrityDegraded: true }, intelligence, {
      confidence: 0.8,
      replayDegraded: true,
    });
    expect(trust.operationalSteadiness).toContain("Operational stability remains strong");
    expect(trust.uncertaintyTransparent).toBe(true);
    expect(trust.restrainedUrgency).toBeDefined();
  });
});

describe("humanRealism", () => {
  it("avoids dramatization with calm reassurance", () => {
    const intelligence = computeInvisibleOperationalIntelligence({}, { recentlyResolved: true, confidence: 0.9 });
    const human = assessHumanRealism({}, intelligence, { recentlyResolved: true, confidence: 0.9 });
    expect(human.calmReassurance).toContain("without dramatization");
    expect(human.emotionalSteadiness).toBe(true);
  });

  it("compresses multiple recommendations into companion phrase", () => {
    const intelligence = computeInvisibleOperationalIntelligence({ pendingRecommendations: 4, replayIntegrityDegraded: true });
    const human = assessHumanRealism(
      { pendingRecommendations: 4, replayIntegrityDegraded: true },
      intelligence,
      { priorityIssue: "replay continuity during extended operational sessions" },
    );
    expect(human.companionPhrase).toContain("highest-impact unresolved area");
  });
});

describe("cognitiveAttentionArchitecture", () => {
  it("resolves invisible attention during deep serenity", () => {
    expect(
      resolveCognitiveAttention({
        mood: "elevated",
        flowState: "immersive",
        recovery: false,
        tension: 0.4,
        deepSerenity: true,
      }),
    ).toBe("invisible");
  });

  it("resolves invisible attention during recovery", () => {
    expect(
      resolveCognitiveAttention({
        mood: "stable",
        flowState: "recovering",
        recovery: true,
        tension: 0.1,
      }),
    ).toBe("invisible");
  });
});

describe("narrativeCompressionV4", () => {
  it("converges multi-event signals with stability reassurance", () => {
    const compressed = compressOperationalEventsV4({
      replayAlertCount: 5,
      telemetryAlertCount: 3,
      recommendationCount: 4,
      recoveryNotices: 1,
    });
    expect(compressed).toHaveLength(1);
    expect(compressed[0]).toContain("continues across extended operational sessions");
    expect(compressed[0]).toContain("operational stability remains steady");
  });

  it("integrates serenity recovery into narrative", () => {
    const partnership = computeCognitivePartnership({}, { recentlyResolved: true, confidence: 0.88 });
    const narrative = buildOperationalNarrative({
      priorityIssue: "replay continuity",
      confidence: 0.88,
      confidenceLabel: "strong",
      recentlyResolved: true,
      serenity: partnership.serenity,
      humanRealism: partnership.humanRealism,
    });
    expect(narrative.recoveryStory).toContain("steady state");
  });
});

describe("invisibleCognitivePartnership", () => {
  it("orchestrates full partnership stack", () => {
    const partnership = computeCognitivePartnership({});
    expect(partnership.intelligence).toBeDefined();
    expect(partnership.partnership).toBeDefined();
    expect(partnership.serenity).toBeDefined();
    expect(partnership.trustPresence).toBeDefined();
    expect(partnership.humanRealism).toBeDefined();
    expect(partnership.partnershipClassName).toContain("mc-flow-sustained");
  });
});
