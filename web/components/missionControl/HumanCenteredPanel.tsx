"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAmbientBrief,
  fetchCollaborationSessions,
  fetchConversation,
  fetchContinuityMemory,
  fetchCopilot,
  fetchHumanMarketplace,
  fetchHumanOverview,
  fetchLifeOS,
  fetchLivePresence,
  fetchLivingOverview,
  fetchMobileEdge,
  fetchMultimodalVoice,
  fetchPendingActions,
  fetchPersonalIntelligence,
  fetchRelationalState,
  fetchThinkingBoundaries,
  fetchTrustControls,
  fetchTrustCenter,
  fetchUniversalChannels,
  fetchVoiceStatus,
  fetchWorldClassExplainability,
  optInLifeOS,
  optInPersonalIntelligence,
  deleteOperatorMemory,
  proposeAction,
  setOperatorStyle,
  startCollaborationSession,
} from "@/lib/missionControl/humanApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const titles: Record<string, string> = {
  "human-overview": "Human-Centered OS",
  "human-relational": "Relational Intelligence",
  "human-voice": "Voice & Presence",
  "human-channels": "Universal Channels",
  "human-life": "LifeOS",
  "human-actions": "Action Runtime",
  "human-ambient": "Ambient Presence",
  "human-collaboration": "Collaboration Sessions",
  "human-trust": "Trust Center",
  "human-marketplace": "Marketplace",
  "human-mobile": "Mobile & Edge",
  "human-living": "Living Companion",
  "human-live-presence": "Live Presence",
  "human-conversation": "Conversation Continuity",
  "human-copilot": "Operational Co-Pilot",
  "human-personal": "Personal Intelligence",
  "human-explainability": "World-Class Explainability",
  "human-thinking": "Thinking Boundaries",
  "human-multimodal-voice": "Multimodal Voice",
  "human-continuity": "Continuity Memory",
  "human-trust-controls": "Trust Controls",
};

export function HumanCenteredPanel({ view }: Props) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "human-overview") setData(await fetchHumanOverview());
      else if (view === "human-relational") setData(await fetchRelationalState());
      else if (view === "human-voice") setData(await fetchVoiceStatus());
      else if (view === "human-channels") setData(await fetchUniversalChannels());
      else if (view === "human-life") setData(await fetchLifeOS());
      else if (view === "human-actions") setData(await fetchPendingActions());
      else if (view === "human-ambient") setData(await fetchAmbientBrief());
      else if (view === "human-collaboration") setData(await fetchCollaborationSessions());
      else if (view === "human-trust") setData(await fetchTrustCenter());
      else if (view === "human-marketplace") setData(await fetchHumanMarketplace());
      else if (view === "human-mobile") setData(await fetchMobileEdge());
      else if (view === "human-living") setData(await fetchLivingOverview());
      else if (view === "human-live-presence") setData(await fetchLivePresence());
      else if (view === "human-conversation") setData(await fetchConversation());
      else if (view === "human-copilot") setData(await fetchCopilot());
      else if (view === "human-personal") setData(await fetchPersonalIntelligence());
      else if (view === "human-explainability") setData(await fetchWorldClassExplainability());
      else if (view === "human-thinking") setData(await fetchThinkingBoundaries());
      else if (view === "human-multimodal-voice") setData(await fetchMultimodalVoice());
      else if (view === "human-continuity") setData(await fetchContinuityMemory());
      else if (view === "human-trust-controls") setData(await fetchTrustControls());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const title = titles[view] ?? "Human-Centered OS";

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16, color: mcColors.textBright }}>{title}</h2>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()} disabled={busy}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {view === "human-overview" && data ? (
        <div style={cardStyle}>
          <div style={{ fontWeight: 600 }}>{String(data.identity ?? data.vision ?? "Living operational companion")}</div>
          <div style={{ color: mcColors.textDim, marginTop: 6 }}>{String(data.mission ?? data.principle ?? "")}</div>
          <div style={{ color: mcColors.textMuted, marginTop: 8, fontSize: 12 }}>
            Phase {String(data.phase ?? "10.1")} — autonomous execution blocked:{" "}
            {String(data.autonomous_execution_blocked ?? true)}
          </div>
          {(data.impossible_feeling as Record<string, unknown>)?.reaction_target ? (
            <div style={{ color: mcColors.cyan, marginTop: 8, fontSize: 12, fontStyle: "italic" }}>
              {String((data.impossible_feeling as Record<string, unknown>).reaction_target)}
            </div>
          ) : null}
        </div>
      ) : null}

      {view === "human-relational" && data ? (
        <>
          <div style={cardStyle}>
            Mode:{" "}
            <strong>
              {String(
                ((data.emotional_context as Record<string, unknown>)?.mode as Record<string, unknown>)?.mode ??
                  "companion",
              )}
            </strong>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["companion", "operator", "mentor", "executive", "crisis"].map((mode) => (
              <button
                key={mode}
                type="button"
                style={mcButtonSecondaryStyle}
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  void setOperatorStyle("default", mode)
                    .then(() => load())
                    .finally(() => setBusy(false));
                }}
              >
                {mode}
              </button>
            ))}
          </div>
        </>
      ) : null}

      {view === "human-voice" && data ? (
        <div style={cardStyle}>
          <div>Channels: {JSON.stringify((data as { channels?: string[] }).channels ?? [])}</div>
          <div style={{ marginTop: 6, color: mcColors.amber }}>
            {String((data as { policy?: { governance_invariant?: string } }).policy?.governance_invariant ?? "")}
          </div>
          <p style={{ marginTop: 10, fontSize: 12, color: mcColors.textMuted }}>
            Enable in chat: set <code>VOICE_SURFACE_ENABLED=true</code>, then{" "}
            <code>VOICE_INPUT_ENABLED</code> / <code>VOICE_OUTPUT_ENABLED</code>. Optional Whisper STT:{" "}
            <code>VOICE_STT_PROVIDER=whisper</code> + OpenAI key. Premium TTS:{" "}
            <code>VOICE_TTS_PROVIDER=elevenlabs</code>.
          </p>
        </div>
      ) : null}

      {view === "human-channels" && data ? (
        <div>
          {((data.channels as Array<Record<string, unknown>>) ?? []).map((ch) => (
            <div key={String(ch.name)} style={cardStyle}>
              <strong>{String(ch.label ?? ch.name)}</strong> — {String(ch.status)} — governed: {String(ch.governed)}
            </div>
          ))}
        </div>
      ) : null}

      {view === "human-life" && data ? (
        <>
          <div style={cardStyle}>Opted in: {String(data.opted_in ?? false)}</div>
          {!data.opted_in ? (
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void optInLifeOS("default")
                  .then(() => load())
                  .finally(() => setBusy(false));
              }}
            >
              Opt in to LifeOS
            </button>
          ) : null}
        </>
      ) : null}

      {view === "human-actions" && data ? (
        <>
          <div style={cardStyle}>Pending actions: {String(data.count ?? 0)}</div>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void proposeAction("slack_post", "default")
                .then(() => load())
                .finally(() => setBusy(false));
            }}
          >
            Propose sample Slack post
          </button>
          {((data.pending as Array<Record<string, unknown>>) ?? []).map((a) => (
            <div key={String(a.action_id)} style={cardStyle}>
              {String(a.action_type)} — {String(a.status)} — {String(a.action_id)}
            </div>
          ))}
        </>
      ) : null}

      {view === "human-ambient" && data ? (
        <div style={cardStyle}>
          <div style={{ fontWeight: 600 }}>{String((data.away_brief as Record<string, unknown>)?.title ?? "While you were away")}</div>
          <pre style={{ whiteSpace: "pre-wrap", marginTop: 8, fontSize: 12, color: mcColors.textDim }}>
            {String((data.away_brief as Record<string, unknown>)?.brief ?? "")}
          </pre>
        </div>
      ) : null}

      {view === "human-collaboration" && data ? (
        <>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void startCollaborationSession("default", "investigation", "MC session")
                .then(() => load())
                .finally(() => setBusy(false));
            }}
          >
            Start collaboration session
          </button>
          {((data.sessions as Array<Record<string, unknown>>) ?? []).map((s) => (
            <div key={String(s.session_id)} style={cardStyle}>
              {String(s.session_id)} — {String(s.focus)} — {String(s.status)}
            </div>
          ))}
        </>
      ) : null}

      {view === "human-trust" && data ? (
        <div style={cardStyle}>
          Trust score: <strong>{String(data.trust_score ?? "—")}</strong>
          <div style={{ marginTop: 6, fontSize: 12, color: mcColors.textDim }}>
            {JSON.stringify(data.safety_boundaries ?? {}, null, 2)}
          </div>
        </div>
      ) : null}

      {view === "human-marketplace" && data ? (
        <div>
          {((data.plugins as Array<Record<string, unknown>>) ?? []).map((p) => (
            <div key={String(p.plugin_id ?? p.name)} style={cardStyle}>
              {String((p.manifest as Record<string, unknown>)?.name ?? p.name ?? p.plugin_id)}
            </div>
          ))}
        </div>
      ) : null}

      {view === "human-mobile" && data ? (
        <div style={{ ...cardStyle, marginBottom: 10 }}>
          <strong>PWA</strong>
          <div style={{ marginTop: 6, fontSize: 12, color: mcColors.textMuted }}>
            Installable: {String((data.pwa as { pwa_installable?: boolean })?.pwa_installable ?? true)} · Push:{" "}
            {String((data.pwa as { web_push_enabled?: boolean })?.web_push_enabled ?? false)} · Subscriptions:{" "}
            {String((data.pwa as { subscriptions?: number })?.subscriptions ?? 0)}
          </div>
          <p style={{ marginTop: 8, fontSize: 12, color: mcColors.textMuted }}>
            Enable push with <code>WEB_PUSH_ENABLED=true</code> and VAPID keys. Users opt in from the chat install
            banner.
          </p>
        </div>
      ) : null}

      {view === "human-mobile" && data ? (
        <div style={cardStyle}>
          Edge: {String((data.edge as Record<string, unknown>)?.edge_enabled ?? false)} — Offline:{" "}
          {String((data.edge as Record<string, unknown>)?.offline_mode ?? false)}
        </div>
      ) : null}

      {view === "human-living" && data ? (
        <div style={cardStyle}>
          <div style={{ fontWeight: 600 }}>{String(data.identity ?? "Living companion")}</div>
          <div style={{ marginTop: 6, color: mcColors.textDim }}>{String(data.mission ?? "")}</div>
        </div>
      ) : null}

      {view === "human-live-presence" && data ? (
        <>
          <div style={cardStyle}>
            <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 12 }}>
              {String((data.nudge as Record<string, unknown>)?.nudge ?? "")}
            </pre>
          </div>
          <div style={cardStyle}>Stream items: {String(((data.stream as Record<string, unknown>)?.stream as unknown[])?.length ?? 0)}</div>
        </>
      ) : null}

      {view === "human-conversation" && data ? (
        <div style={cardStyle}>
          <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 12, color: mcColors.textDim }}>
            {String((data.resume as Record<string, unknown>)?.resume_core ?? (data.resume as Record<string, unknown>)?.resume_text ?? (data.status as Record<string, unknown>)?.resume_preview ?? "")}
          </pre>
        </div>
      ) : null}

      {view === "human-copilot" && data ? (
        <>
          <div style={cardStyle}>{String((data.hypotheses as Record<string, unknown>)?.explanation ?? "")}</div>
          {(((data.hypotheses as Record<string, unknown>)?.hypotheses as Array<Record<string, unknown>>) ?? []).map((h, i) => (
            <div key={i} style={cardStyle}>
              {String(h.hypothesis)} — confidence: {String(h.confidence)}
            </div>
          ))}
        </>
      ) : null}

      {view === "human-personal" && data ? (
        <>
          <div style={cardStyle}>Opted in: {String(data.opted_in ?? false)}</div>
          {!data.opted_in ? (
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void optInPersonalIntelligence("default")
                  .then(() => load())
                  .finally(() => setBusy(false));
              }}
            >
              Opt in to Personal Intelligence
            </button>
          ) : null}
        </>
      ) : null}

      {view === "human-explainability" && data ? (
        <div style={cardStyle}>
          <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 12, color: mcColors.textDim }}>
            {String(data.narrative ?? "")}
          </pre>
          <div style={{ marginTop: 8 }}>Trust score: {String(data.trust_score ?? "—")}</div>
        </div>
      ) : null}

      {view === "human-thinking" && data ? (
        <div style={cardStyle}>
          <div style={{ fontWeight: 600 }}>{String(data.principle ?? "Think continuously. Act only with governance.")}</div>
          <div style={{ marginTop: 8, fontSize: 12 }}>Allowed: {JSON.stringify(data.allowed ?? [])}</div>
          <div style={{ marginTop: 4, fontSize: 12, color: mcColors.amber }}>Forbidden: {JSON.stringify(data.forbidden ?? [])}</div>
        </div>
      ) : null}

      {view === "human-multimodal-voice" && data ? (
        <div style={cardStyle}>
          Features: {JSON.stringify((data.features as Record<string, unknown>) ?? {}, null, 2)}
        </div>
      ) : null}

      {view === "human-continuity" && data ? (
        <>
          <div style={cardStyle}>
            Phase: {String(((data.memory as Record<string, unknown>)?.record as Record<string, unknown>)?.phase ?? "—")}
            {" — "}
            Focus: {String(((data.memory as Record<string, unknown>)?.record as Record<string, unknown>)?.focus ?? "—")}
          </div>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>
            {String((data.resume as Record<string, unknown>)?.resume_core ?? "")}
          </pre>
        </>
      ) : null}

      {view === "human-trust-controls" && data ? (
        <>
          <div style={cardStyle}>{String(data.principle ?? "")}</div>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void deleteOperatorMemory("default")
                .then(() => load())
                .finally(() => setBusy(false));
            }}
          >
            Delete all operator memory
          </button>
        </>
      ) : null}

      {!data && !error ? <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</p> : null}
    </section>
  );
}
