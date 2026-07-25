/** Tracked work jobs API — Mission Control Jobs tab. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type TrackedJobRecord = {
  id: string;
  title: string;
  job_type: string;
  status: string;
  source?: string;
  session_id?: string;
  created_at?: number;
  updated_at?: number;
  completed_at?: string | number;
  result?: string | null;
  full_result?: string | null;
  failure_reason?: string | null;
  result_preview?: string | null;
  result_summary?: string | null;
  provider_used?: string | null;
  model_used?: string | null;
  params?: Record<string, unknown>;
};

export type JobsGrouped = {
  queued: TrackedJobRecord[];
  running: TrackedJobRecord[];
  completed: TrackedJobRecord[];
  failed: TrackedJobRecord[];
  cancelled: TrackedJobRecord[];
};

export type TrackedJobsResponse = {
  jobs: TrackedJobRecord[];
  grouped: JobsGrouped;
  count: number;
};

export const fetchTrackedJobs = () => mcFetch<TrackedJobsResponse>("/api/v1/jobs");

export const cancelTrackedJob = (jobId: string) =>
  mcFetch<TrackedJobRecord>(`/api/v1/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
    body: "{}",
  });

export function emptyJobsGrouped(): JobsGrouped {
  return { queued: [], running: [], completed: [], failed: [], cancelled: [] };
}

export function hasActiveTrackedJobs(grouped: JobsGrouped): boolean {
  return grouped.running.length > 0 || grouped.queued.length > 0;
}

const PROVIDER_JOB_TYPES = new Set([
  "research_plan",
  "comparison_brief",
  "roadmap_generation",
  "architecture_summary",
  "planning_document",
]);

const EXTERNAL_JOB_TYPES = new Set(["external_health_report"]);

export function usesProviderJobType(jobType: string): boolean {
  return PROVIDER_JOB_TYPES.has(jobType);
}

export function usesExternalJobType(jobType: string): boolean {
  return EXTERNAL_JOB_TYPES.has(jobType);
}

export function externalJobTarget(job: TrackedJobRecord): string {
  const target = job.params?.target;
  return typeof target === "string" && target ? target : "external";
}

export function externalJobMode(job: TrackedJobRecord): string {
  const mode = job.params?.external_mode ?? job.params?.mode;
  return typeof mode === "string" && mode ? mode : "public";
}

export function jobControlHint(status: string): string {
  switch (status) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "cancelled":
      return "Cancelled";
    default:
      return status;
  }
}

export function normalizeJobsGrouped(input: unknown): JobsGrouped {
  const o = input as Partial<JobsGrouped> | null;
  if (!o || typeof o !== "object") return emptyJobsGrouped();
  return {
    queued: dedupeJobsById(Array.isArray(o.queued) ? o.queued : []),
    running: dedupeJobsById(Array.isArray(o.running) ? o.running : []),
    completed: dedupeJobsById(Array.isArray(o.completed) ? o.completed : []),
    failed: dedupeJobsById(Array.isArray(o.failed) ? o.failed : []),
    cancelled: dedupeJobsById(Array.isArray(o.cancelled) ? o.cancelled : []),
  };
}

/** Canonical identity for Mission Control job lists — last write wins by updated_at. */
export function dedupeJobsById(items: TrackedJobRecord[]): TrackedJobRecord[] {
  const byId = new Map<string, TrackedJobRecord>();
  for (const job of items) {
    if (!job?.id) continue;
    const existing = byId.get(job.id);
    if (!existing) {
      byId.set(job.id, job);
      continue;
    }
    const existingTs = existing.updated_at ?? existing.created_at ?? 0;
    const nextTs = job.updated_at ?? job.created_at ?? 0;
    if (nextTs >= existingTs) byId.set(job.id, job);
  }
  return [...byId.values()].sort((a, b) => (b.updated_at ?? b.created_at ?? 0) - (a.updated_at ?? a.created_at ?? 0));
}
