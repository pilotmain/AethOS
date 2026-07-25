"use client";

import { JobsActionsPanel } from "@/components/JobsActionsPanel";
import { JobsTrackedWorkPanel } from "@/components/JobsTrackedWorkPanel";
import type { ActionsGrouped } from "@/lib/missionControl/actions";
import type { JobsGrouped } from "@/lib/missionControl/trackedJobs";

type Props = {
  actions: ActionsGrouped;
  jobs: JobsGrouped;
  onRefresh: () => void;
};

/** Operator-visible runtime actions — includes governed mutation approvals (preflights). */
export function RuntimeActionsPanel({ actions, jobs, onRefresh }: Props) {
  return (
    <>
      <JobsTrackedWorkPanel jobs={jobs} onRefresh={onRefresh} mode="all" />
      <div style={{ marginTop: 24 }}>
        <JobsActionsPanel actions={actions} onRefresh={onRefresh} />
      </div>
    </>
  );
}
