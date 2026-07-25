/** Phase 10.1.5.1 — Focus Canvas data shaping and progressive depth layers. */

import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import { OVERVIEW_QUICK_VIEWS } from "@/lib/missionControl/sidebarNavigation";
import type { MissionControlView } from "@/lib/missionControl/views";

import { confidenceLabel } from "./spatialHierarchy";

export type FocusCanvasState = {
  headline: string;
  priorityIssue: string;
  confidence: number;
  confidenceLabel: string;
  summary: string;
  reasoning: string;
  replayDetail: string;
  fullDetail: string;
  collaborationContext: string;
  attentionLevel: "informational" | "elevated" | "urgent";
};

export function buildFocusCanvasState(
  brief: Record<string, unknown> | null,
  quality: Record<string, unknown> | null,
): FocusCanvasState {
  const investigation = (brief?.investigation_companion as Record<string, unknown>) ?? {};
  const reasoning = (brief?.operational_reasoning as Record<string, unknown>) ?? {};
  const replay = (brief?.deep_replay as Record<string, unknown>) ?? {};
  const metrics = (quality?.metrics as Record<string, number>) ?? {};

  const priorityIssue =
    String(brief?.remaining_risk ?? "").trim() ||
    "replay continuity during long-running sessions";

  const confidence = Number(brief?.confidence ?? metrics.trust_retention ?? 0.72);
  const summaryText = String(brief?.brief ?? brief?.brief_core ?? "").trim();
  const summary = firstParagraph(summaryText);

  const headline =
    `The most important unresolved issue right now is ${priorityIssue.replace(/^the /i, "")}.`;

  const reasoningText = String(reasoning.synthesis ?? "").trim();
  const replayText = [
    String(replay.compressed_summary ?? replay.narrative ?? "").trim(),
    ...(Array.isArray(replay.investigation_branches)
      ? (replay.investigation_branches as string[]).slice(0, 3).map((b) => `- ${b}`)
      : []),
  ]
    .filter(Boolean)
    .join("\n");

  const collaboration = String(investigation.narrative ?? "").split("\n")[0]?.trim() ?? "";

  return {
    headline,
    priorityIssue,
    confidence,
    confidenceLabel: confidenceLabel(confidence),
    summary: summary || "Operational focus is stabilizing replay integrity and companion trust.",
    reasoning: reasoningText,
    replayDetail: replayText,
    fullDetail: summaryText,
    collaborationContext: collaboration,
    attentionLevel: confidence < 0.65 ? "elevated" : "informational",
  };
}

export function firstParagraph(text: string): string {
  const parts = text.split(/\n\n+/).map((p) => p.trim()).filter(Boolean);
  return parts[0] ?? text.slice(0, 280);
}

export type ProgressiveDepth = 0 | 1 | 2 | 3;

export function depthLabel(depth: ProgressiveDepth): string | null {
  switch (depth) {
    case 0:
      return "Show replay reasoning";
    case 1:
      return "Show evidence lineage";
    case 2:
      return "Show full operational detail";
    default:
      return null;
  }
}

export function contentForDepth(state: FocusCanvasState, depth: ProgressiveDepth): string {
  if (depth >= 3) return state.fullDetail;
  if (depth >= 2) return [state.summary, state.reasoning, state.replayDetail].filter(Boolean).join("\n\n");
  if (depth >= 1) return [state.summary, state.reasoning].filter(Boolean).join("\n\n");
  return state.summary;
}

const EXECUTIVE_QUICK: MissionControlView[] = [
  "operational-anomalies",
  "recommendation-queue",
  "trust-metrics",
];

const DEEP_QUICK: MissionControlView[] = [
  "companion-replay-intelligence",
  "integrity-routes",
  "operation-preflights",
];

export function quickViewsForMode(mode: MissionControlMode) {
  if (mode === "executive") {
    return OVERVIEW_QUICK_VIEWS.filter((v) => EXECUTIVE_QUICK.includes(v.id));
  }
  if (mode === "deep-engineering") {
    const deep = OVERVIEW_QUICK_VIEWS.filter((v) => DEEP_QUICK.includes(v.id));
    const base = OVERVIEW_QUICK_VIEWS.filter((v) => !DEEP_QUICK.includes(v.id)).slice(0, 2);
    return [...deep, ...base];
  }
  return OVERVIEW_QUICK_VIEWS.slice(0, 4);
}

export function showConnectionHealth(mode: MissionControlMode): boolean {
  return mode !== "executive";
}

export function showMetricStrip(mode: MissionControlMode): boolean {
  return mode !== "executive";
}
