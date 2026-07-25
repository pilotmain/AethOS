/** FIX 311 — Public product experience (experience ≠ platform authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PublicProductExperienceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  public_product_compose_artifacts_only: boolean;
  public_product_authority: boolean;
  automatic_customer_onboarding_enabled: boolean;
  trust_mutation_authority: boolean;
  provider_mutation_authority: boolean;
  tenant_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  public_product_experience?: Record<string, unknown>;
  markdown?: string;
};

export type PublicProductExperienceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  public_product_experience_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPublicProductExperience = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PublicProductExperienceResponse>(
    `/api/v1/mission-control/public-product-experience?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPublicProductExperienceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<PublicProductExperienceRecordResponse>(`/api/v1/mission-control/public-product-experience`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      kind,
      content,
      domain,
    }),
  });

export type PublicExperienceFocus =
  | "public_product_dashboard"
  | "capability_explorer"
  | "trust_explorer"
  | "guided_product_tour"
  | "customer_journey_explorer"
  | "public_education_center";

export const PUBLIC_EXPERIENCE_FOCUS_BY_VIEW: Record<string, PublicExperienceFocus> = {
  "public-product-experience": "public_product_dashboard",
  "public-capability-explorer": "capability_explorer",
  "public-trust-explorer": "trust_explorer",
  "public-product-tour": "guided_product_tour",
  "public-customer-journey": "customer_journey_explorer",
  "public-education-center": "public_education_center",
};
