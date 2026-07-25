/** FIX 304 — channel integration foundation (integration ≠ duplication). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ChannelIntegrationFoundationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  channel_integration_compose_artifacts_only: boolean;
  channel_authority: boolean;
  automatic_channel_provisioning_enabled: boolean;
  cross_channel_identity_bypass_enabled: boolean;
  cross_tenant_channel_access_enabled: boolean;
  authorization_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  channel_integration_foundation?: Record<string, unknown>;
  markdown?: string;
};

export type ChannelIntegrationFoundationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  channel_integration_foundation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlChannelIntegrationFoundation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ChannelIntegrationFoundationResponse>(
    `/api/v1/mission-control/channel-integration-foundation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlChannelIntegrationFoundationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  channel?: string,
) =>
  mcFetch<ChannelIntegrationFoundationRecordResponse>(
    `/api/v1/mission-control/channel-integration-foundation/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        channel,
      }),
    },
  );
