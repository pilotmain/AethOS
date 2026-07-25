/** FIX 181–186 — dogfood pilot manual gate closure (compose-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type DogfoodPilotGateClosureChecklistItem = {
  fix: string;
  gate: string;
  passed: boolean;
  blockers?: string[];
  signals?: Record<string, unknown>;
};

export type DogfoodPilotGateClosureResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_reexecution_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  blockers?: string[];
  dogfood_pilot_gate_closure?: {
    gate_complete?: boolean;
    gates_passed?: number;
    gates_total?: number;
    checklist?: DogfoodPilotGateClosureChecklistItem[];
    next_phase?: string | null;
  };
};

export const fetchMissionControlDogfoodPilotGateClosure = (sessionId = "default") =>
  mcFetch<DogfoodPilotGateClosureResponse>(
    `/api/v1/mission-control/dogfood-pilot-gate-closure?session_id=${encodeURIComponent(sessionId)}`,
  );
