/** Provider-specific evidence rendering — shared orchestration UI edge. */

import type { ExecutionEvidenceItem } from "@/lib/missionControl/operationPreflight";

export function providerEvidenceSourceLabel(source: string | undefined): string {
  if (!source) return "";
  switch (source) {
    case "railway_api":
      return "Railway API";
    case "github_api":
      return "GitHub API";
    case "vercel_api":
      return "Vercel API";
    case "provider_api":
      return "Provider API";
    case "browser_fallback":
      return "Browser fallback";
    case "memory":
      return "Operational memory";
    case "local_probe":
      return "Local probe";
    default:
      return source.replace(/_/g, " ");
  }
}

const OPERATION_EVIDENCE_TITLES: Record<string, Record<string, string>> = {
  railway: {
    list_deployments: "Railway deployment evidence",
    project_details: "Railway service evidence",
    check_logs: "Railway log evidence",
    why_down: "Railway diagnostic evidence",
    inspect_failed_deployment: "Railway deployment inspection evidence",
  },
  github: {
    workflow_runs: "GitHub workflow evidence",
    workflow_jobs: "GitHub workflow job evidence",
    workflow_diagnostic: "GitHub workflow diagnostic evidence",
  },
  vercel: {
    list_domains: "Vercel domain evidence",
    list_deployments: "Vercel deployment evidence",
    project_details: "Vercel project evidence",
    check_logs: "Vercel log evidence",
    why_down: "Vercel diagnostic evidence",
    inspect_failed_deployment: "Vercel deployment inspection evidence",
  },
};

export function providerEvidenceSectionTitle(provider: string, operationType?: string): string {
  const byOp = OPERATION_EVIDENCE_TITLES[provider];
  if (operationType && byOp?.[operationType]) return byOp[operationType];
  if (provider === "railway") return "Railway evidence";
  if (provider === "github") return "GitHub evidence";
  if (provider === "vercel") return "Vercel evidence";
  return "Evidence";
}

const EVIDENCE_TYPE_LABELS: Record<string, Record<string, string>> = {
  railway: {
    deployment: "Deployment",
    deployment_state: "Deployment state",
    service_details: "Service details",
    log_excerpt: "Log excerpt",
    diagnosis: "Diagnosis",
  },
  github: {
    workflow_run: "Workflow run",
    workflow_job: "Workflow job",
    check_run: "Check run",
    failure_reason: "Failure reason",
    diagnosis: "Diagnosis",
  },
  vercel: {
    domain_record: "Domain",
    deployment_state: "Deployment",
    project_metadata: "Project metadata",
    failure_reason: "Failure reason",
    log_excerpt: "Log excerpt",
    diagnosis: "Diagnosis",
  },
};

export function providerEvidenceTypeLabel(provider: string, evidenceType: string | undefined): string {
  if (!evidenceType) return "Record";
  const labels = EVIDENCE_TYPE_LABELS[provider];
  return labels?.[evidenceType] ?? evidenceType.replace(/_/g, " ");
}

export function formatProviderEvidenceItem(
  provider: string,
  item: ExecutionEvidenceItem,
): string {
  const parts: string[] = [];
  const sourceLabel = providerEvidenceSourceLabel(item.source);
  const typeLabel = providerEvidenceTypeLabel(provider, item.type);
  if (sourceLabel) parts.push(sourceLabel);
  if (typeLabel) parts.push(typeLabel);
  if (item.confidence) {
    parts.push(`[${String(item.confidence).replace(/_/g, " ")}]`);
  }
  const header = parts.length > 0 ? `${parts.join(" · ")}: ` : "";
  return `${header}${item.message ?? ""}`.trim();
}
