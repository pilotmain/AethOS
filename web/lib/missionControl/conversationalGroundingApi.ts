import { mcFetch } from "@/lib/missionControl/fetch";

export type ConversationalGroundingState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  operational_grounding?: { summary?: string; grounded?: boolean };
  continuity_thread?: { summary?: string; reconstructed?: boolean; continuity_confidence?: number };
  operational_partner?: { summary?: string; investigation_aware?: boolean };
  telegram_persistence?: { summary?: string; hydrated?: boolean };
  governance_restraint?: { summary?: string; suppress_footer?: boolean };
  conversational_realism?: { summary?: string; realism_active?: boolean };
  strategic_position?: Record<string, string>;
  principles?: Record<string, string>;
  cross_surface_convergence?: { summary?: string; converged?: boolean };
  live_operational_grounding?: { summary?: string; converged?: boolean };
};

export const fetchConversationalGroundingState = (sessionId = "default") =>
  mcFetch<ConversationalGroundingState>(
    `/api/v1/conversational-operational-grounding/state?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchContinuityReconstruction = (sessionId = "default") =>
  mcFetch<ConversationalGroundingState["continuity_thread"]>(
    `/api/v1/conversational-operational-grounding/continuity-reconstruction?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchOperationalContext = (sessionId = "default") =>
  mcFetch<{ ok: boolean; primary_subject?: string; has_memory?: boolean }>(
    `/api/v1/conversational-operational-grounding/operational-context?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchGovernanceRestraint = () =>
  mcFetch<ConversationalGroundingState["governance_restraint"]>(
    "/api/v1/conversational-operational-grounding/governance-restraint",
  );

export const fetchConversationalRealism = () =>
  mcFetch<ConversationalGroundingState["conversational_realism"]>(
    "/api/v1/conversational-operational-grounding/conversational-realism",
  );

export const fetchTelegramPersistence = (sessionId = "default") =>
  mcFetch<ConversationalGroundingState["telegram_persistence"]>(
    `/api/v1/conversational-operational-grounding/telegram-persistence?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchPartnerPresence = (sessionId = "default") =>
  mcFetch<ConversationalGroundingState["operational_partner"]>(
    `/api/v1/conversational-operational-grounding/partner-presence?session_id=${encodeURIComponent(sessionId)}`,
  );

export const fetchCrossSurfaceConvergence = (sessionId = "default", channel = "chat") =>
  mcFetch<ConversationalGroundingState["cross_surface_convergence"]>(
    `/api/v1/conversational-operational-grounding/cross-surface-convergence?session_id=${encodeURIComponent(sessionId)}&channel=${encodeURIComponent(channel)}`,
  );

export const fetchLiveOperationalGrounding = (sessionId = "default", channel = "chat") =>
  mcFetch<ConversationalGroundingState["live_operational_grounding"]>(
    `/api/v1/conversational-operational-grounding/live-operational-grounding?session_id=${encodeURIComponent(sessionId)}&channel=${encodeURIComponent(channel)}`,
  );
