/** FIX 130 — cross-lane timeline → lane detail navigation (read-only). */

import type { MissionControlCrossLaneSnapshot } from "@/lib/missionControl/missionControlCrossLaneApi";

export type CrossLaneLaneId =
  | "software_delivery"
  | "railway_orchestration"
  | "production_governance"
  | "incident_command"
  | "multi_agent_collaboration"
  | "route_diagnostics"
  | "durable_jobs";

export type LaneDetailRow = { label: string; value: string };

export type LaneDetailBlock = {
  lane: string;
  anchorId: string;
  title: string;
  rows: LaneDetailRow[];
};

const LANE_LABELS: Record<string, string> = {
  software_delivery: "Software delivery",
  railway_orchestration: "Railway orchestration",
  production_governance: "Production governance",
  incident_command: "Incident command",
  multi_agent_collaboration: "Agent collaboration",
  route_diagnostics: "Route diagnostics",
  durable_jobs: "Durable jobs",
};

export function laneAnchorId(lane: string): string {
  return `mc-lane-${lane.replace(/_/g, "-")}`;
}

export function laneDisplayTitle(lane: string): string {
  return LANE_LABELS[lane] ?? lane.replace(/_/g, " ");
}

export function laneDataFromSnapshot(
  snapshot: MissionControlCrossLaneSnapshot,
  lane: string,
): Record<string, unknown> {
  const lanes = snapshot.lanes ?? {};
  if (lane === "incident_command") {
    return (snapshot.incident_linkage as Record<string, unknown>) ?? lanes.incident_command ?? {};
  }
  if (lane === "production_governance") {
    return (snapshot.rollout_visibility as Record<string, unknown>) ?? lanes.production_governance ?? {};
  }
  if (lane === "multi_agent_collaboration") {
    return (
      (snapshot.agent_collaboration_summary as Record<string, unknown>) ??
      lanes.multi_agent_collaboration ??
      {}
    );
  }
  return (lanes[lane] as Record<string, unknown>) ?? {};
}

export function buildLaneDetailBlock(
  snapshot: MissionControlCrossLaneSnapshot,
  lane: string,
): LaneDetailBlock {
  const data = laneDataFromSnapshot(snapshot, lane);
  return {
    lane,
    anchorId: laneAnchorId(lane),
    title: laneDisplayTitle(lane),
    rows: extractLaneDetailRows(lane, data),
  };
}

export function extractLaneDetailRows(lane: string, data: Record<string, unknown>): LaneDetailRow[] {
  switch (lane) {
    case "software_delivery":
      return [
        { label: "Plan id", value: String(data.plan_id ?? "—") },
        { label: "Status", value: String(data.plan_status ?? "—") },
        { label: "Repository", value: String(data.repository ?? "—") },
        {
          label: "Pending gates",
          value: Array.isArray(data.pending_gates)
            ? (data.pending_gates as string[]).join(", ") || "none"
            : "none",
        },
        { label: "Timeline events", value: String(data.timeline_event_count ?? 0) },
        {
          label: "Agent collaboration",
          value: data.agent_collaboration ? "linked" : "none",
        },
      ];
    case "railway_orchestration":
      return [
        { label: "Recent journals", value: String(data.recent_journals ?? 0) },
        { label: "Recent receipts", value: String(data.recent_receipts ?? 0) },
        { label: "Latest status", value: String(data.latest_journal_status ?? "—") },
        { label: "Execution id", value: String(data.latest_execution_id ?? "—") },
        { label: "Note", value: String(data.note ?? "—") },
      ];
    case "incident_command":
      return [
        { label: "Open incidents", value: String(data.open_incidents ?? 0) },
        { label: "Total recorded", value: String(data.incident_count ?? 0) },
        { label: "Latest id", value: String(data.latest_incident_id ?? "—") },
        { label: "Latest status", value: String(data.latest_status ?? "—") },
      ];
    case "production_governance":
      return [
        { label: "Rollout records", value: String(data.rollout_records ?? 0) },
        { label: "Shadow records", value: String(data.shadow_records ?? 0) },
        { label: "Latest stage", value: String(data.latest_rollout_stage ?? "—") },
        { label: "Policy", value: String(data.mutation_policy ?? "—") },
      ];
    case "multi_agent_collaboration":
      return [
        { label: "Collaboration id", value: String(data.collaboration_id ?? "—") },
        { label: "Status", value: String(data.status ?? "—") },
        {
          label: "Agents run",
          value: Array.isArray(data.agents_run) ? (data.agents_run as string[]).join(", ") || "—" : "—",
        },
        {
          label: "Mutation",
          value: data.mutation_performed === false ? "none (advisory)" : String(data.mutation_performed ?? "—"),
        },
      ];
    case "route_diagnostics":
      return [
        { label: "Route id", value: String(data.route_id ?? "—") },
        { label: "Matched module", value: String(data.matched_module ?? "—") },
        { label: "Intent", value: String(data.intent ?? "—") },
        { label: "Recorded at", value: String(data.recorded_at ?? "—") },
      ];
    case "durable_jobs":
      return [
        { label: "Job graph nodes", value: String(data.node_count ?? 0) },
        {
          label: "Mutation job types",
          value: data.mutation_job_types_blocked ? "blocked (governed)" : String(data.mutation_job_types_blocked ?? "—"),
        },
      ];
    default:
      return [{ label: "Lane", value: lane }, { label: "Signal", value: data.ok ? "observed" : "no signal" }];
  }
}

export function scrollToLaneAnchor(lane: string): void {
  if (typeof document === "undefined") return;
  const el = document.getElementById(laneAnchorId(lane));
  el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
