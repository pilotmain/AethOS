/** Enterprise readiness — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type DoctorCheck = {
  name?: string;
  status?: "PASS" | "WARNING" | "FAIL";
  category?: string;
  detail?: string;
  fix_hint?: string;
  actionable?: {
    what_failed?: string;
    likely_cause?: string;
    what_to_check?: string;
    next_command?: string;
    where_for_details?: string;
  };
};

export type DoctorResult = {
  ok: boolean;
  overall?: string;
  summary?: string;
  counts?: Record<string, number>;
  checks?: DoctorCheck[];
};

export type SetupStep = {
  id?: string;
  title?: string;
  doc?: string;
  completed?: boolean;
  status?: string;
};

export type HealthDashboard = {
  ok?: boolean;
  overall?: string;
  doctor_overall?: string;
  components?: Record<string, { status?: string; detail?: string; global_score?: number }>;
  demo?: { enabled?: boolean; label?: string };
};

export const fetchEnterpriseDoctor = (category?: string) =>
  mcFetch<DoctorResult>(`/api/v1/enterprise/doctor${category ? `?category=${encodeURIComponent(category)}` : ""}`);

export const fetchEnterpriseConfig = () => mcFetch<Record<string, unknown>>("/api/v1/enterprise/config");

export const fetchEnterpriseHealth = () => mcFetch<HealthDashboard>("/api/v1/enterprise/health");

export const fetchSetupWizard = () =>
  mcFetch<{ ok: boolean; steps?: SetupStep[]; progress?: number; next_step?: SetupStep; complete?: boolean }>(
    "/api/v1/enterprise/setup-wizard"
  );

export const fetchSafeDefaults = () => mcFetch<{ ok: boolean; violations?: string[]; checks?: Record<string, boolean> }>(
  "/api/v1/enterprise/safe-defaults"
);

export const fetchDemoStatus = () => mcFetch<{ enabled?: boolean; label?: string; overlay?: Record<string, unknown> }>("/api/v1/enterprise/demo");

export const enableDemoMode = () => mcFetch<{ ok: boolean; enabled?: boolean }>("/api/v1/enterprise/demo/enable", { method: "POST" });

export const disableDemoMode = () => mcFetch<{ ok: boolean; enabled?: boolean }>("/api/v1/enterprise/demo/disable", { method: "POST" });
