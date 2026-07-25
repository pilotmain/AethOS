/** FIX 137B — Mission Control replay deep links (URL + link refs). */

import type { MissionControlTimelineEntry } from "@/lib/missionControl/missionControlCrossLaneApi";
import type { ApprovalAuditRecord } from "@/lib/missionControl/missionControlApprovalExecutionApi";

export type ReplayDeepLinkTarget = {
  link?: string;
  linkKey?: string;
  linkRef?: string;
  stepIndex?: number;
  jobId?: string;
};

export type OperatorUrlState = ReplayDeepLinkTarget & {
  view?: string;
};

const VIEW_PARAM = "mc_view";
const LINK_PARAM = "mc_link";
const STEP_PARAM = "mc_step";
const JOB_PARAM = "mc_job";

export function buildTimelineLinkRef(entry: MissionControlTimelineEntry): string {
  const lane = entry.lane ?? "";
  const action = entry.action ?? "";
  const timestamp = entry.timestamp ?? "";
  return `timeline:${lane}:${action}:${timestamp}`;
}

export function buildAuditLinkRef(audit: ApprovalAuditRecord): string {
  return `audit:${audit.approval_id ?? ""}`;
}

export function buildEvidenceLinkRef(receipt: Record<string, unknown>): string {
  const recordedAt = String(receipt.recorded_at ?? "");
  const phase = String(receipt.phase ?? receipt.status ?? "receipt");
  const sourceFile = String(receipt.source_file ?? "");
  return `evidence:${recordedAt}:${phase}:${sourceFile}`;
}

export function readOperatorUrlState(): OperatorUrlState {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const view = params.get(VIEW_PARAM) ?? undefined;
  const link = params.get(LINK_PARAM) ?? undefined;
  const stepRaw = params.get(STEP_PARAM);
  const jobId = params.get(JOB_PARAM) ?? undefined;
  const stepIndex = stepRaw != null && stepRaw !== "" ? Number(stepRaw) : undefined;
  return {
    view,
    link,
    linkKey: link,
    linkRef: link,
    stepIndex: Number.isFinite(stepIndex) ? stepIndex : undefined,
    jobId,
  };
}

export function writeOperatorUrlState(state: OperatorUrlState): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  if (state.view) params.set(VIEW_PARAM, state.view);
  else params.delete(VIEW_PARAM);

  const link = state.link ?? state.linkRef ?? state.linkKey;
  if (link) params.set(LINK_PARAM, link);
  else params.delete(LINK_PARAM);

  if (state.stepIndex != null && state.stepIndex >= 0) params.set(STEP_PARAM, String(state.stepIndex));
  else params.delete(STEP_PARAM);

  if (state.jobId) params.set(JOB_PARAM, state.jobId);
  else params.delete(JOB_PARAM);

  const qs = params.toString();
  const next = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
  window.history.replaceState(null, "", next);
}

export function buildReplayNavigationTarget(target: ReplayDeepLinkTarget): OperatorUrlState {
  return {
    view: "mission-job-replay",
    link: target.link ?? target.linkRef ?? target.linkKey,
    linkRef: target.linkRef ?? target.link,
    linkKey: target.linkKey ?? target.link,
    stepIndex: target.stepIndex,
    jobId: target.jobId,
  };
}
