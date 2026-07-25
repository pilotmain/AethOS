/** FIX 129–131 — Mission Control cross-lane snapshot + lane drilldown API (read-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionControlAttentionItem = {
  lane?: string;
  gate?: string;
  priority?: string;
  count?: number;
};

export type MissionControlTimelineEntry = {
  lane?: string;
  timestamp?: string;
  action?: string;
  detail?: string;
};

export type MissionControlCrossLaneSnapshot = {
  snapshot_id?: string;
  schema_version?: string;
  session_id?: string;
  correlation_id?: string;
  plan_id?: string;
  observed_lanes?: string[];
  mutation_performed?: boolean;
  recorded_at?: string;
  lanes?: Record<string, Record<string, unknown>>;
  unified_timeline?: MissionControlTimelineEntry[];
  execution_health?: Record<string, unknown>;
  attention_queue?: MissionControlAttentionItem[];
  active_approvals?: MissionControlAttentionItem[];
  rollout_visibility?: Record<string, unknown>;
  incident_linkage?: Record<string, unknown>;
  agent_collaboration_summary?: Record<string, unknown>;
};

export type MissionControlCrossLaneSnapshotResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  route_id: string;
  detail?: string;
  snapshot: MissionControlCrossLaneSnapshot;
};

export type LaneDrilldownSection = {
  section_id: string;
  title: string;
  kind: string;
  empty_message?: string;
  rows?: Array<{ label: string; value: string }>;
  items?: Array<Record<string, unknown>>;
};

export type LaneDrilldownResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  schema_version: string;
  lane: string;
  session_id: string;
  detail?: string;
  sections: LaneDrilldownSection[];
};

export const fetchMissionControlCrossLaneSnapshot = (sessionId = "default") =>
  mcFetch<MissionControlCrossLaneSnapshotResponse>(
    `/api/v1/mission-control/cross-lane/snapshot?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchMissionControlLaneDrilldown = (laneId: string, sessionId = "default") =>
  mcFetch<LaneDrilldownResponse>(
    `/api/v1/mission-control/cross-lane/lane/${encodeURIComponent(laneId)}/drilldown?session_id=${encodeURIComponent(sessionId)}`,
  );
