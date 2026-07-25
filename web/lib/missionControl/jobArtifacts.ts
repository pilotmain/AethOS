/** Mission Control artifact helpers — full report lives here, not in chat. */

import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export function jobFullReport(job: TrackedJobRecord): string {
  const full = job.full_result ?? job.result;
  return (full ?? "").trim();
}

export function jobArtifactPreview(job: TrackedJobRecord): string {
  return (job.result_preview ?? "").trim();
}

export function jobArtifactSummary(job: TrackedJobRecord): string {
  return (job.result_summary ?? "").trim();
}

export function downloadFilename(job: TrackedJobRecord): string {
  const slug = (job.title || job.job_type || "artifact")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
  return `${slug || "job"}-${job.id}.md`;
}

export function downloadArtifactMarkdown(job: TrackedJobRecord): void {
  const text = jobFullReport(job);
  if (!text) return;
  const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = downloadFilename(job);
  a.click();
  URL.revokeObjectURL(url);
}

export async function copyArtifactText(job: TrackedJobRecord): Promise<boolean> {
  const text = jobFullReport(job);
  if (!text || typeof navigator === "undefined" || !navigator.clipboard) {
    return false;
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/** Chat completion events must not embed the full artifact body. */
export function chatMessageLooksLikeSummaryOnly(message: string, fullReport: string): boolean {
  const msg = message.trim();
  const full = fullReport.trim();
  if (!full || full.length < 400) return true;
  if (msg.includes(full)) return false;
  if (full.length > 600 && msg.length < full.length * 0.5) return true;
  return msg.includes("Summary:") || msg.includes("Mission Control");
}
