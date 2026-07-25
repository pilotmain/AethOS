"use client";

import { useState } from "react";
import {
  CHAT_ASSISTANT_MESSAGE_MAX,
  CHAT_USER_MESSAGE_MAX,
  isWideArtifactContent,
  operationalEventTone,
} from "@/lib/chat/layout";
import { mcAlpha, mcCardStyle, mcColors } from "@/lib/missionControl/layout";
import { ChatAgentMetaBadges } from "@/components/chat/ChatAgentMetaBadges";
import type { CachedMessage } from "@/lib/chat/lanes";
import type { ChatProgressEvent } from "@/lib/chat/types";

const TONE_COLORS = {
  neutral: mcColors.textMuted,
  progress: "var(--aethos-accent)",
  success: mcColors.green,
  warning: mcColors.amber,
  error: mcColors.red,
};

type Props = {
  message: CachedMessage;
  streaming?: boolean;
};

function ProgressStepIcon({ status, live }: { status?: string; live: boolean }) {
  if (status === "done") {
    return <span style={{ color: mcColors.green, fontSize: 12, lineHeight: "16px" }}>✓</span>;
  }
  if (status === "failed") {
    return <span style={{ color: mcColors.amber, fontSize: 12, lineHeight: "16px" }}>⚠</span>;
  }
  return live ? (
    <span className="chat-progress-spin" aria-hidden />
  ) : (
    <span style={{ color: mcColors.textMuted, fontSize: 12, lineHeight: "16px" }}>•</span>
  );
}

/**
 * §3 — live activity feed. Renders incoming step/thought events as a growing
 * checklist while the turn runs, then collapses to an expandable summary once it
 * finishes. Read-only visibility: it mirrors what the tool loop reported.
 */
function ChatProgressFeed({ progress, live }: { progress: ChatProgressEvent[]; live: boolean }) {
  const steps = progress.filter((p) => p.type === "step");
  const anyRunning = steps.some((p) => p.status === "running");
  const liveNow = live || anyRunning;
  const [override, setOverride] = useState<boolean | null>(null);
  if (progress.length === 0) return null;
  const expanded = override ?? liveNow;
  const accent = "var(--aethos-accent)";
  const header = liveNow
    ? "Working…"
    : `Worked through ${steps.length} step${steps.length === 1 ? "" : "s"}`;
  return (
    <div
      style={{
        marginBottom: 10,
        border: `1px solid ${mcAlpha(accent, 18)}`,
        borderRadius: 12,
        background: mcAlpha(accent, 5),
        overflow: "hidden",
      }}
    >
      <button
        type="button"
        onClick={() => setOverride(!expanded)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          padding: "7px 12px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: accent,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
        }}
        aria-expanded={expanded}
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          {liveNow ? <span className="chat-progress-spin" aria-hidden /> : null}
          {header}
        </span>
        <span aria-hidden style={{ fontSize: 10 }}>{expanded ? "▾" : "▸"}</span>
      </button>
      {expanded ? (
        <ol
          style={{
            listStyle: "none",
            margin: 0,
            padding: "2px 12px 10px",
            display: "flex",
            flexDirection: "column",
            gap: 6,
          }}
        >
          {progress.map((p, i) =>
            p.type === "thought" ? (
              <li
                key={`t-${i}`}
                style={{
                  paddingLeft: 24,
                  fontSize: 12,
                  fontStyle: "italic",
                  color: mcColors.textMuted,
                  lineHeight: 1.45,
                }}
              >
                {p.text}
              </li>
            ) : (
              <li
                key={p.id ?? `s-${i}`}
                style={{ display: "flex", gap: 8, alignItems: "flex-start" }}
              >
                <span style={{ width: 16, flexShrink: 0, marginTop: 1, textAlign: "center" }}>
                  <ProgressStepIcon status={p.status} live={liveNow} />
                </span>
                <span
                  style={{
                    fontSize: 12.5,
                    lineHeight: 1.45,
                    color: p.status === "failed" ? mcColors.amber : mcColors.text,
                  }}
                >
                  {p.summary || p.action || p.tool || "Working"}
                </span>
              </li>
            ),
          )}
        </ol>
      ) : null}
    </div>
  );
}

export function OperationalMessageCard({ message, streaming }: Props) {
  const tone = operationalEventTone(message.event_type);
  const accent = TONE_COLORS[tone];
  return (
    <article
      className="chat-operational-card chat-fade-in"
      style={{
        ...mcCardStyle,
        width: "100%",
        padding: "12px 16px 12px 20px",
        borderLeft: `3px solid ${accent}`,
        boxShadow: tone === "progress" ? `0 0 24px ${mcAlpha(accent, 13)}` : mcCardStyle.boxShadow,
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
      }}
    >
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          marginTop: 6,
          background: accent,
          boxShadow: tone === "progress" ? `0 0 10px ${accent}` : "none",
          flexShrink: 0,
        }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        {message.event_type ? (
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: accent,
              marginBottom: 4,
            }}
          >
            {message.event_type.replace(/_/g, " ")}
          </div>
        ) : null}
        <div
          style={{
            fontSize: 13,
            lineHeight: 1.55,
            color: mcColors.text,
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content || (streaming ? "" : "—")}
          {streaming ? <span className="chat-stream-cursor" aria-hidden /> : null}
        </div>
      </div>
    </article>
  );
}

export function ChatMessageBubble({ message, streaming }: Props) {
  if (message.role === "system" || message.id.startsWith("jevt-") || message.id.startsWith("evt-")) {
    return <OperationalMessageCard message={message} streaming={streaming} />;
  }

  const isUser = message.role === "user";
  const wideArtifact = !isUser && isWideArtifactContent(message.content);
  const maxWidth = wideArtifact ? "100%" : isUser ? CHAT_USER_MESSAGE_MAX : CHAT_ASSISTANT_MESSAGE_MAX;

  return (
    <article
      className={`chat-message-bubble chat-fade-in ${streaming ? "chat-message-streaming" : ""}`}
      style={{
        alignSelf: isUser ? "flex-end" : "flex-start",
        width: wideArtifact ? "100%" : "auto",
        maxWidth,
        padding: wideArtifact ? "16px 18px" : "12px 16px",
        borderRadius: wideArtifact ? 16 : isUser ? 16 : 18,
        background: isUser ? "rgba(34,211,238,0.08)" : "rgba(255,255,255,0.04)",
        border: `1px solid ${isUser ? "rgba(34,211,238,0.22)" : "rgba(255,255,255,0.1)"}`,
        boxShadow: wideArtifact ? "0 8px 32px rgba(0,0,0,0.28)" : "0 4px 20px rgba(0,0,0,0.15)",
        whiteSpace: "pre-wrap",
        fontSize: wideArtifact ? 13 : 14,
        lineHeight: 1.55,
      }}
    >
      {wideArtifact ? (
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: mcColors.textDim,
            marginBottom: 10,
          }}
        >
          Operational report
        </div>
      ) : null}
      {!isUser && message.progress && message.progress.length > 0 ? (
        <ChatProgressFeed live={!!streaming} progress={message.progress} />
      ) : null}
      <div style={{ color: isUser ? mcColors.text : "inherit" }}>
        {message.content || (streaming ? "" : "")}
        {streaming && !message.content ? (
          <span className="chat-stream-cursor" aria-hidden />
        ) : null}
      </div>
      {!isUser && message.meta && Object.keys(message.meta).length > 0 ? (
        <ChatAgentMetaBadges meta={message.meta} />
      ) : null}
    </article>
  );
}
