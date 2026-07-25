"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import { readTrackedActionIds, getOrCreateChatSessionId } from "@/lib/chat/actionLifecycleBridge";
import { readTrackedBrowserSessionIds } from "@/lib/chat/browserLifecycleBridge";
import { readTrackedJobIds } from "@/lib/chat/jobLifecycleBridge";
import { fetchChatBrainContext, fetchMemoryRecall, type ChatBrainContext, type MemoryRecallMatch } from "@/lib/chat/chatBrainApi";
import { fetchResearchNotes, pinResearchNote } from "@/lib/missionControl/phase4Api";
import { fetchSessionGroup, linkSessionIds, type SessionGroup } from "@/lib/chat/sessionLinkApi";
import { fetchEngineeringContext } from "@/lib/missionControl/localWorkspaceApi";
import { buildMissionControlUrl, buildResearchReplayUrl, missionControlHref } from "@/lib/missionControl/deepLinks";
import { mcColors } from "@/lib/missionControl/layout";
import type { ModelCatalogSnapshot } from "@/lib/chat/modelSelection";
import type { CachedMessage } from "@/lib/chat/lanes";
import type { ChatHealth } from "@/lib/connection/chatHealth";

type Props = {
  messages: CachedMessage[];
  health: ChatHealth | null;
  effectiveModel?: ModelCatalogSnapshot["effective"] | null;
};

// Progressive-disclosure rail section (§3). Lighter than a bordered card: a
// subtle top divider + an accessible toggle instead of boxing every widget.
// Only the 2-3 most relevant blocks open by default; the rest collapse.
function ContextCard({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section style={{ borderTop: `1px solid ${mcColors.borderSubtle}` }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          padding: "12px 2px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: mcColors.textDim,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.04em",
        }}
      >
        <span>{title.toUpperCase()}</span>
        <span
          aria-hidden
          style={{
            fontSize: 14,
            lineHeight: 1,
            transition: "transform 0.15s ease",
            transform: open ? "rotate(90deg)" : "none",
          }}
        >
          ›
        </span>
      </button>
      {open ? <div style={{ padding: "0 2px 14px" }}>{children}</div> : null}
    </section>
  );
}

export function ChatContextPanel({ messages, health, effectiveModel }: Props) {
  const jobIds = readTrackedJobIds();
  const actionIds = readTrackedActionIds();
  const browserIds = readTrackedBrowserSessionIds();
  const [engineering, setEngineering] = useState<Awaited<ReturnType<typeof fetchEngineeringContext>> | null>(null);
  const [brain, setBrain] = useState<ChatBrainContext | null>(null);
  const [recallQuery, setRecallQuery] = useState("");
  const [recallLoading, setRecallLoading] = useState(false);
  const [recallError, setRecallError] = useState<string | null>(null);
  const [recallMatches, setRecallMatches] = useState<MemoryRecallMatch[]>([]);
  const [recallRan, setRecallRan] = useState(false);
  const [sessionGroup, setSessionGroup] = useState<SessionGroup | null>(null);
  const [linkTarget, setLinkTarget] = useState("");
  const [linkBusy, setLinkBusy] = useState(false);
  const [linkMsg, setLinkMsg] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, unknown>[]>([]);
  const [pinText, setPinText] = useState("");
  const [pinBusy, setPinBusy] = useState(false);

  useEffect(() => {
    const sessionId = getOrCreateChatSessionId();
    void fetchEngineeringContext(sessionId)
      .then(setEngineering)
      .catch(() => setEngineering(null));
    void fetchChatBrainContext(sessionId)
      .then(setBrain)
      .catch(() => setBrain(null));
    void fetchSessionGroup(sessionId)
      .then(setSessionGroup)
      .catch(() => setSessionGroup(null));
    void fetchResearchNotes(sessionId)
      .then((res) => setNotes(res.notes ?? []))
      .catch(() => setNotes([]));
  }, [messages.length]);

  const recentOperational = messages
    .filter((m) => m.role === "system" || m.id.startsWith("jevt-") || m.id.startsWith("evt-"))
    .slice(-4)
    .reverse();

  const latestAgentMeta = [...messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.meta && Object.keys(m.meta).length > 0)?.meta;

  const sessionKey = latestAgentMeta?.session_key;
  const researchReplay = latestAgentMeta?.research_replay_id;
  const agentLane = latestAgentMeta?.lane ?? latestAgentMeta?.route_id;
  const toolCalls = latestAgentMeta?.agent_tool_calls;

  const ws = engineering?.active_workspace;
  const git = engineering?.git;

  const brainReplayId = brain?.research?.replay_id ?? (researchReplay ? String(researchReplay) : "");
  const researchLibraryHref = brainReplayId
    ? buildResearchReplayUrl(brainReplayId)
    : buildMissionControlUrl("deep-research");

  const runMemoryRecall = async () => {
    const q = recallQuery.trim();
    if (!q) return;
    setRecallLoading(true);
    setRecallError(null);
    try {
      const result = await fetchMemoryRecall(q, 6);
      setRecallRan(true);
      if (!result.ok) {
        setRecallMatches([]);
        setRecallError(result.error === "vector_memory_disabled" ? "Vector memory is off." : "Recall failed.");
        return;
      }
      setRecallMatches(result.matches ?? []);
    } catch {
      setRecallMatches([]);
      setRecallError("Recall failed.");
    } finally {
      setRecallLoading(false);
    }
  };

  const linkTelegramSession = async () => {
    const target = linkTarget.trim();
    if (!target) return;
    const sessionId = getOrCreateChatSessionId();
    setLinkBusy(true);
    setLinkMsg(null);
    try {
      const group = await linkSessionIds([sessionId, target], sessionId);
      if (!group) {
        setLinkMsg("Link failed.");
        return;
      }
      setSessionGroup(group);
      setLinkTarget("");
      setLinkMsg("Sessions linked — research memory shared across Telegram and web.");
      void fetchChatBrainContext(sessionId).then(setBrain).catch(() => setBrain(null));
    } catch {
      setLinkMsg("Link failed.");
    } finally {
      setLinkBusy(false);
    }
  };

  const pinCurrentNote = async () => {
    const sessionId = getOrCreateChatSessionId();
    const text =
      pinText.trim() ||
      (brain?.research?.query ? String(brain.research.query) : "") ||
      (messages.find((m) => m.role === "user")?.content || "").slice(0, 200);
    if (!text.trim()) return;
    setPinBusy(true);
    try {
      await pinResearchNote(sessionId, {
        text: text.trim(),
        replay_id: brain?.research?.replay_id ?? (researchReplay ? String(researchReplay) : undefined),
        query: brain?.research?.query,
      });
      setPinText("");
      const res = await fetchResearchNotes(sessionId);
      setNotes(res.notes ?? []);
    } finally {
      setPinBusy(false);
    }
  };

  return (
    <aside
      className="chat-context-panel"
      style={{
        width: 340,
        flexShrink: 0,
        borderLeft: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.28)",
        overflowY: "auto",
        padding: "16px 14px",
      }}
    >
      <ContextCard title="Runtime status" defaultOpen>
        <p style={{ margin: 0, fontSize: 13, color: health?.chatReady ? mcColors.green : mcColors.red }}>
          {health?.connectionLabel ?? "Checking API…"}
        </p>
      </ContextCard>

      <ContextCard title="Engineering context">
        {ws ? (
          <>
            <p style={{ margin: "0 0 4px", fontSize: 13, color: mcColors.text, fontWeight: 600 }}>{ws.name}</p>
            <p style={{ margin: "0 0 8px", fontSize: 11, color: mcColors.textDim, wordBreak: "break-all" }}>{ws.path}</p>
            {git?.branch ? (
              <p style={{ margin: "0 0 4px", fontSize: 12, color: mcColors.textMuted }}>
                Branch: {git.branch} · modified {git.modified_count ?? 0} · untracked {git.untracked_count ?? 0}
              </p>
            ) : null}
            {engineering?.architecture_summary ? (
              <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.textMuted, lineHeight: 1.45 }}>
                {(engineering.architecture_summary || "").slice(0, 180)}
                {(engineering.architecture_summary || "").length > 180 ? "…" : ""}
              </p>
            ) : null}
            {engineering?.dependency_severity ? (
              <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.amber }}>
                Dependency severity: {engineering.dependency_severity}
              </p>
            ) : null}
          </>
        ) : (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            No active workspace. Try: <code style={{ fontSize: 11 }}>register local repo /path</code>
          </p>
        )}
        <Link href={missionControlHref("home")} style={{ fontSize: 12, color: "var(--aethos-accent)", display: "inline-block", marginTop: 8 }}>
          Engineering in Mission Control →
        </Link>
      </ContextCard>

      {(sessionKey || researchReplay || agentLane || toolCalls) ? (
        <ContextCard title="Agent activity">
          {sessionKey ? (
            <p style={{ margin: "0 0 6px", fontSize: 11, fontFamily: "monospace", color: mcColors.cyan, wordBreak: "break-all" }}>
              session: {String(sessionKey)}
            </p>
          ) : null}
          {researchReplay ? (
            <p style={{ margin: "0 0 6px", fontSize: 11, fontFamily: "monospace", color: mcColors.textMuted }}>
              research: {String(researchReplay)}
            </p>
          ) : null}
          {agentLane ? (
            <p style={{ margin: "0 0 6px", fontSize: 12, color: mcColors.textMuted }}>
              lane: {String(agentLane)}
            </p>
          ) : null}
          {toolCalls ? (
            <p style={{ margin: "0 0 6px", fontSize: 12, color: mcColors.textMuted }}>
              tool calls: {String(toolCalls)}
            </p>
          ) : null}
          {latestAgentMeta?.comparison_html_url ? (
            <a
              href={(() => {
                const url = String(latestAgentMeta.comparison_html_url);
                if (url.startsWith("http")) return url;
                const base =
                  typeof window !== "undefined"
                    ? process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8010"
                    : "";
                return `${base}${url}`;
              })()}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 12, color: "var(--aethos-accent)", display: "inline-block", marginTop: 8 }}
            >
              Open comparison page →
            </a>
          ) : null}
          <Link
            href={researchReplay ? buildResearchReplayUrl(String(researchReplay)) : buildMissionControlUrl("deep-research")}
            style={{ fontSize: 12, color: "var(--aethos-accent)", display: "inline-block", marginTop: 8, marginRight: 12 }}
          >
            Research replay →
          </Link>
          <Link href={missionControlHref("agents")} style={{ fontSize: 12, color: "var(--aethos-accent)", display: "inline-block", marginTop: 8 }}>
            Orchestration →
          </Link>
        </ContextCard>
      ) : null}

      <ContextCard title="Agent model" defaultOpen>
        {effectiveModel ? (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted, lineHeight: 1.5 }}>
            <strong style={{ color: mcColors.cyan }}>{effectiveModel.label}</strong>
            <span style={{ display: "block", fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>
              {effectiveModel.provider}/{effectiveModel.model} · source: {effectiveModel.source}
            </span>
          </p>
        ) : (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>Resolving agent model…</p>
        )}
      </ContextCard>

      <ContextCard title="Memory &amp; research">
        {brain?.memory?.enabled ? (
          <>
            <p style={{ margin: "0 0 6px", fontSize: 12, color: mcColors.textMuted }}>
              Vector memory · {brain.memory.backend} · {brain.memory.entry_count} entries
            </p>
            {(brain.memory.recent ?? []).slice(0, 3).map((row) => (
              <p
                key={String(row.id)}
                style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.textMuted, lineHeight: 1.45 }}
              >
                {(row.text || "").slice(0, 120)}
                {(row.text || "").length > 120 ? "…" : ""}
              </p>
            ))}
          </>
        ) : (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            Memory is turned off for this deployment — ask AethOS in chat how to enable it to pin operational facts.
          </p>
        )}
        {brain?.research?.replay_id ? (
          <p style={{ margin: "8px 0 0", fontSize: 11, fontFamily: "monospace", color: mcColors.cyan }}>
            Last research: {brain.research.replay_id}
            {brain.research.query ? (
              <span style={{ display: "block", fontFamily: "inherit", color: mcColors.textMuted, marginTop: 4 }}>
                {(brain.research.query || "").slice(0, 100)}
                {(brain.research.query || "").length > 100 ? "…" : ""}
              </span>
            ) : null}
          </p>
        ) : researchReplay ? (
          <p style={{ margin: "8px 0 0", fontSize: 11, fontFamily: "monospace", color: mcColors.textMuted }}>
            Active turn replay: {String(researchReplay)}
          </p>
        ) : (
          <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.textDim }}>
            No saved research for this chat session yet.
          </p>
        )}
        <div style={{ marginTop: 12 }}>
          <p style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.textDim }}>
            Link Telegram session (e.g. tg-12345-99)
          </p>
          {sessionGroup?.linked_session_ids && sessionGroup.linked_session_ids.length > 1 ? (
            <p style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.cyan, lineHeight: 1.45 }}>
              Linked: {(sessionGroup.linked_session_ids ?? []).join(" · ")}
            </p>
          ) : null}
          <div style={{ display: "flex", gap: 6 }}>
            <input
              value={linkTarget}
              onChange={(e) => setLinkTarget(e.target.value)}
              placeholder="tg-chat-user"
              style={{
                flex: 1,
                minWidth: 0,
                padding: "6px 8px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.35)",
                color: mcColors.text,
                fontSize: 12,
              }}
            />
            <button
              type="button"
              disabled={linkBusy || !linkTarget.trim()}
              onClick={() => void linkTelegramSession()}
              style={{
                padding: "6px 10px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(34,211,238,0.12)",
                color: mcColors.cyan,
                fontSize: 11,
                fontWeight: 600,
                cursor: linkBusy ? "wait" : "pointer",
              }}
            >
              {linkBusy ? "…" : "Link"}
            </button>
          </div>
          {linkMsg ? (
            <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.green }}>{linkMsg}</p>
          ) : null}
        </div>
        <div style={{ marginTop: 12 }}>
          <p style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.textDim }}>
            Pinned notes
          </p>
          {(notes ?? []).slice(0, 3).map((note) => (
            <p key={String(note.id)} style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.textMuted, lineHeight: 1.45 }}>
              {(String(note.text || "")).slice(0, 140)}
            </p>
          ))}
          <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
            <input
              value={pinText}
              onChange={(e) => setPinText(e.target.value)}
              placeholder="Pin research takeaway…"
              style={{
                flex: 1,
                minWidth: 0,
                padding: "6px 8px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.35)",
                color: mcColors.text,
                fontSize: 12,
              }}
            />
            <button
              type="button"
              disabled={pinBusy}
              onClick={() => void pinCurrentNote()}
              style={{
                padding: "6px 10px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(34,211,238,0.12)",
                color: mcColors.cyan,
                fontSize: 11,
                fontWeight: 600,
                cursor: pinBusy ? "wait" : "pointer",
              }}
            >
              Pin
            </button>
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          <p style={{ margin: "0 0 6px", fontSize: 11, color: mcColors.textDim }}>
            Recall across chats (vector memory)
          </p>
          <div style={{ display: "flex", gap: 6 }}>
            <input
              type="search"
              value={recallQuery}
              onChange={(e) => setRecallQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void runMemoryRecall();
              }}
              placeholder="deployment status, railway…"
              style={{
                flex: 1,
                minWidth: 0,
                padding: "6px 8px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.35)",
                color: mcColors.text,
                fontSize: 12,
              }}
            />
            <button
              type="button"
              disabled={recallLoading || !recallQuery.trim()}
              onClick={() => void runMemoryRecall()}
              style={{
                padding: "6px 10px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(34,211,238,0.12)",
                color: mcColors.cyan,
                fontSize: 11,
                fontWeight: 600,
                cursor: recallLoading ? "wait" : "pointer",
              }}
            >
              {recallLoading ? "…" : "Recall"}
            </button>
          </div>
          {recallError ? (
            <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.amber }}>{recallError}</p>
          ) : null}
          {recallMatches.length > 0 ? (
            <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none" }}>
              {recallMatches.map((row) => (
                <li
                  key={String(row.id ?? row.text)}
                  style={{
                    padding: "6px 0",
                    borderTop: `1px solid ${mcColors.borderSubtle}`,
                    fontSize: 11,
                    color: mcColors.textMuted,
                    lineHeight: 1.45,
                  }}
                >
                  {row.score != null ? (
                    <span style={{ color: mcColors.cyan, marginRight: 6 }}>{Math.round(row.score * 100)}%</span>
                  ) : null}
                  {(row.text || "").slice(0, 140)}
                  {(row.text || "").length > 140 ? "…" : ""}
                </li>
              ))}
            </ul>
          ) : recallRan && !recallLoading && !recallError ? (
            <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.textDim }}>No matches.</p>
          ) : null}
        </div>
        <Link
          href={researchLibraryHref}
          style={{ fontSize: 12, color: "var(--aethos-accent)", display: "inline-block", marginTop: 8 }}
        >
          Open research library →
        </Link>
      </ContextCard>

      <ContextCard title="Tracked work" defaultOpen>
        <p style={{ margin: "0 0 6px", fontSize: 13, color: mcColors.text }}>
          {jobIds.length} job{jobIds.length === 1 ? "" : "s"} tracked
        </p>
        {jobIds.slice(-3).map((id) => (
          <div key={id} style={{ fontSize: 11, color: mcColors.textDim, fontFamily: "monospace", marginBottom: 4 }}>
            {id}
          </div>
        ))}
      </ContextCard>

      <ContextCard title="Runtime actions">
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
          {actionIds.length} action{actionIds.length === 1 ? "" : "s"} in session
        </p>
      </ContextCard>

      <ContextCard title="Browser sessions">
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
          {browserIds.length} session{browserIds.length === 1 ? "" : "s"} tracked
        </p>
      </ContextCard>

      {recentOperational.length > 0 ? (
        <ContextCard title="Latest lifecycle">
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
            {recentOperational.map((m) => (
              <li
                key={m.id}
                style={{
                  padding: "8px 0",
                  borderBottom: `1px solid ${mcColors.borderSubtle}`,
                  color: mcColors.textMuted,
                  lineHeight: 1.45,
                }}
              >
                {(m.content || "").slice(0, 120)}
                {(m.content || "").length > 120 ? "…" : ""}
              </li>
            ))}
          </ul>
        </ContextCard>
      ) : null}
    </aside>
  );
}
