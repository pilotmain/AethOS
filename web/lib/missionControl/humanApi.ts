/** Phase 10.0+ — Human-centered agentic OS API client (backend-aligned via mcFetch). */

import { mcFetch } from "@/lib/missionControl/fetch";

const API = "/api/v1/human";

export function fetchHumanOverview(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/overview?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchRelationalState(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/relational?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchVoiceStatus(channel = "web_voice") {
  return mcFetch<Record<string, unknown>>(`${API}/voice?channel=${encodeURIComponent(channel)}`);
}

export function fetchUniversalChannels() {
  return mcFetch<{ channels?: Array<Record<string, unknown>> }>(`${API}/channels`);
}

export function fetchLifeOS(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/life?session_id=${encodeURIComponent(sessionId)}`);
}

export function optInLifeOS(sessionId = "default", domains?: string[]) {
  return mcFetch<Record<string, unknown>>(`${API}/life/opt-in`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, domains }),
  });
}

export function fetchPendingActions(sessionId?: string) {
  const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return mcFetch<{ pending?: Array<Record<string, unknown>>; count?: number }>(`${API}/actions${q}`);
}

export function proposeAction(actionType: string, sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/actions/propose`, {
    method: "POST",
    body: JSON.stringify({ action_type: actionType, session_id: sessionId }),
  });
}

export function fetchAmbientBrief(sessionId = "default", windowHours = 8) {
  return mcFetch<Record<string, unknown>>(
    `${API}/ambient?session_id=${encodeURIComponent(sessionId)}&window_hours=${windowHours}`,
  );
}

export function fetchCollaborationSessions(operatorId?: string) {
  const q = operatorId ? `?operator_id=${encodeURIComponent(operatorId)}` : "";
  return mcFetch<{ sessions?: Array<Record<string, unknown>> }>(`${API}/collaboration${q}`);
}

export function fetchTrustCenter(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/trust?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchHumanMarketplace() {
  return mcFetch<{ plugins?: Array<Record<string, unknown>> }>(`${API}/marketplace`);
}

export function fetchMobileEdge() {
  return mcFetch<Record<string, unknown>>(`${API}/mobile-edge`);
}

export function fetchLivingOverview(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/living?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchLivePresence(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/live-presence?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchConversation(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/conversation?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchCopilot(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/copilot?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchPersonalIntelligence(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/personal?session_id=${encodeURIComponent(sessionId)}`);
}

export function optInPersonalIntelligence(sessionId = "default", explanationStyle = "balanced") {
  return mcFetch<Record<string, unknown>>(
    `${API}/personal/opt-in?session_id=${encodeURIComponent(sessionId)}&explanation_style=${encodeURIComponent(explanationStyle)}`,
    { method: "POST" },
  );
}

export function fetchThinkingBoundaries(capability?: string) {
  const q = capability ? `?capability=${encodeURIComponent(capability)}` : "";
  return mcFetch<Record<string, unknown>>(`${API}/thinking-boundaries${q}`);
}

export function fetchWorldClassExplainability(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/explainability?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchMultimodalVoice(channel = "web_voice") {
  return mcFetch<Record<string, unknown>>(`${API}/multimodal-voice?channel=${encodeURIComponent(channel)}`);
}

export function fetchHumanRoutes() {
  return mcFetch<{
    ok?: boolean;
    health?: string;
    mounted_routes?: Array<Record<string, unknown>>;
    missing_routes?: Array<Record<string, unknown>>;
  }>(`${API}/routes`);
}

export function fetchRuntimeIntegrity() {
  return mcFetch<Record<string, unknown>>(`${API}/integrity`);
}

export function fetchHumanRuntimeReplay(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/replay?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchContinuityMemory(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/continuity?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchTrustControls(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/trust-controls?session_id=${encodeURIComponent(sessionId)}`);
}

export function deleteOperatorMemory(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/trust-controls/delete-memory?session_id=${encodeURIComponent(sessionId)}`, {
    method: "POST",
  });
}

export function fetchHumanIntuition(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/intuition?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchCompanionBrief(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/companion-brief?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchPresenceQuality(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/presence-quality?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchCalmPresence(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/calm-presence?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchOperationalTimeline(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/timeline?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchLivingExplainability(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/living-explainability?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchRestraintStatus(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/restraint?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchPartnerBrief(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/partner-brief?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchOperationalReasoning(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/operational-reasoning?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchInvestigationCompanion(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/investigation-companion?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchDeepReplay(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/deep-replay?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchEmotionalRealism(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/emotional-realism?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchAttentionAwareness(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/attention-awareness?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchCompanionNarrative(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/companion-narrative?session_id=${encodeURIComponent(sessionId)}`);
}

export function fetchCompanionQuality(sessionId = "default") {
  return mcFetch<Record<string, unknown>>(`${API}/companion-quality?session_id=${encodeURIComponent(sessionId)}`);
}

export function setOperatorStyle(sessionId: string, preferredMode: string) {
  return mcFetch<Record<string, unknown>>(`${API}/relational/style`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      preferred_mode: preferredMode,
      verbosity: "medium",
    }),
  });
}

export function startCollaborationSession(operatorId: string, focus: string, context = "") {
  return mcFetch<Record<string, unknown>>(`${API}/collaboration/start`, {
    method: "POST",
    body: JSON.stringify({ operator_id: operatorId, focus, context }),
  });
}
