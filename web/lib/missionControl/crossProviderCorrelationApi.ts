/** Cross-provider deployment correlation — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CrossProviderCorrelationState = {
  ok: boolean;
  session_id?: string;
  updated_at?: string;
  cross_provider_correlation?: {
    github_commit?: string | null;
    github_repo?: string | null;
    vercel_project?: string | null;
    vercel_deployment?: string | null;
    railway_service?: string | null;
    matched_commit?: string | null;
    failure_boundary?: string;
    confidence?: string;
    conclusion?: string;
    needs_binding?: boolean;
    links?: { kind?: string; source?: string; target?: string; confidence?: number; detail?: string }[];
  };
  diagnosis?: {
    failure_boundary?: string;
    confidence?: string;
    conclusion?: string;
    github_status?: string;
    vercel_status?: string;
    railway_status?: string;
  };
};

export const fetchCrossProviderCorrelationState = (sessionId = "default") =>
  mcFetch<CrossProviderCorrelationState>(`/api/v1/correlation/state?session_id=${encodeURIComponent(sessionId)}`);
