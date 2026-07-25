/** FIX 137B — resolve replay deep link to step index. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type JobReplayResolveResponse = {
  ok: boolean;
  read_only?: boolean;
  mutation_performed?: boolean;
  session_id?: string;
  job_id?: string | null;
  link?: string;
  step_index?: number;
  step_id?: string;
  link_key?: string;
  blockers?: string[];
};

export const resolveMissionControlJobReplayLink = (
  sessionId: string,
  link: string,
  jobId?: string,
) => {
  const params = new URLSearchParams({ session_id: sessionId, link });
  if (jobId) params.set("job_id", jobId);
  return mcFetch<JobReplayResolveResponse>(`/api/v1/mission-control/job-replay/resolve?${params.toString()}`);
};
