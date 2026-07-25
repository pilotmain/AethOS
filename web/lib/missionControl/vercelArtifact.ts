/** Vercel read-only job artifacts — structured inventory + collapsed debug. */

import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export type VercelProjectRow = {
  name: string;
  status?: string;
  health?: string;
  production_url?: string | null;
  deployment_state?: string | null;
  attention_reason?: string | null;
  git_repo?: string | null;
};

export type VercelExtractionDebug = {
  current_url?: string;
  page_title?: string;
  candidate_count?: number;
  raw_link_count?: number;
  pipeline?: {
    raw_links_seen?: number;
    project_like_links_seen?: number;
    candidate_names_seen?: number;
    candidates_after_confidence?: number;
    confirmed_projects?: number;
    likely_projects?: number;
    known_memory_matches?: number;
    dashboard_ready?: boolean;
  };
  memory_fallback?: boolean;
  known_memory_projects?: string[];
};

export type VercelInventoryParams = {
  projects?: VercelProjectRow[];
  project_count?: number;
  healthy_count?: number;
  failing_count?: number;
  no_prod_count?: number;
  extraction_method?: string;
  memory_fallback?: boolean;
  extraction_debug?: VercelExtractionDebug;
  ignored_labels?: string[];
  low_confidence_count?: number;
};

const VERCEL_READONLY_TYPES = new Set([
  "vercel_projects_inventory",
  "vercel_service_health_summary",
  "vercel_deployment_status_summary",
]);

export function isVercelReadonlyJob(job: TrackedJobRecord): boolean {
  return VERCEL_READONLY_TYPES.has(job.job_type);
}

export function vercelInventoryFromJob(job: TrackedJobRecord): VercelInventoryParams | null {
  const raw = job.params?.vercel_inventory;
  if (!raw || typeof raw !== "object") return null;
  return raw as VercelInventoryParams;
}

export function isBareZeroProjectSummary(summary: string): boolean {
  const s = summary.trim().toLowerCase();
  return /^-?\s*found\s+0\s+vercel\s+project/.test(s) || s === "found 0 vercel projects";
}

export function isUsefulEmptyExtractionSummary(summary: string): boolean {
  const s = summary.toLowerCase();
  return (
    s.includes("could not confidently") ||
    s.includes("could not identify") ||
    s.includes("reached the vercel dashboard") ||
    s.includes("previously confirmed") ||
    s.includes("memory fallback")
  );
}

export function splitFullReportSections(full: string): {
  main: string;
  debug: string | null;
  extractionDebug: string | null;
} {
  let main = full;
  let debug: string | null = null;
  let extractionDebug: string | null = null;

  const debugMarker = "## Debug extraction";
  const extractionMarker = "## Extraction debug";

  const exIdx = full.indexOf(extractionMarker);
  if (exIdx >= 0) {
    extractionDebug = full.slice(exIdx).trim();
    main = full.slice(0, exIdx).trim();
  }

  const dbgIdx = main.indexOf(debugMarker);
  if (dbgIdx >= 0) {
    debug = main.slice(dbgIdx).trim();
    main = main.slice(0, dbgIdx).trim();
  }

  return { main, debug, extractionDebug };
}

export function operationalSummaryFirst(summary: string): string {
  const s = summary.trim();
  if (!s) return s;
  if (s.startsWith("- ")) return s;
  return s;
}
