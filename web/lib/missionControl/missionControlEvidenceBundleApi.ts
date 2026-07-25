/** FIX 136 — read-only operator evidence bundle export (JSON + Markdown). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionControlEvidenceBundleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  job_id?: string | null;
  detail?: string;
  bundle?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlEvidenceBundle = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  jobId?: string,
) => {
  const params = new URLSearchParams({
    session_id: sessionId,
    format,
  });
  if (jobId) params.set("job_id", jobId);
  return mcFetch<MissionControlEvidenceBundleResponse>(
    `/api/v1/mission-control/evidence-bundle?${params.toString()}`,
  );
};

export function evidenceBundleJsonFilename(sessionId: string, correlationId?: string): string {
  const slug = (correlationId || sessionId).replace(/[^a-zA-Z0-9_-]+/g, "-").slice(0, 48);
  return `aethos-evidence-${slug || "session"}.json`;
}

export function evidenceBundleMarkdownFilename(sessionId: string, correlationId?: string): string {
  const slug = (correlationId || sessionId).replace(/[^a-zA-Z0-9_-]+/g, "-").slice(0, 48);
  return `aethos-evidence-${slug || "session"}.md`;
}

export function downloadTextFile(content: string, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
