/** Browser evidence artifacts — Mission Control Browser tab (Phase 9.8B). */

import { apiBase } from "@/lib/api";
import { mcFetch } from "@/lib/missionControl/fetch";

export type BrowserEvidenceArtifact = {
  artifact_id: string;
  provider?: string;
  created_at?: number;
  session_id?: string;
  source_url?: string;
  capture_type?: string;
  artifact_type?: string;
  headless?: boolean;
  approved?: boolean;
  risk_tier?: string;
  file_path?: string;
  media_type?: string;
  resolution?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  file_exists?: boolean;
  file_size_bytes?: number;
  artifact_file_url?: string;
  file_http_status?: number;
};

export type BrowserEvidenceAuditEvent = {
  at?: number;
  action?: string;
  operator?: string;
  approved?: boolean;
  result?: string;
  target_url?: string;
  capture_type?: string;
  policy_tier?: string;
  session_id?: string;
  artifact_ids?: string[];
  detail?: string;
};

export const fetchBrowserEvidenceArtifacts = (limit = 30) =>
  mcFetch<{ artifacts: BrowserEvidenceArtifact[]; count: number }>(
    `/api/v1/browser/artifacts?limit=${limit}`,
  );

export const fetchBrowserEvidenceAudit = (limit = 50) =>
  mcFetch<{ events: BrowserEvidenceAuditEvent[]; count: number }>(
    `/api/v1/browser/evidence/audit?limit=${limit}`,
  );

export const browserArtifactFileUrl = (artifactId: string) =>
  `${apiBase()}/api/v1/browser/artifacts/${encodeURIComponent(artifactId)}/file`;
