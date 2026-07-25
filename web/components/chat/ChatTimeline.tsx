"use client";

import { ChatMessageBubble } from "@/components/chat/ChatMessageBubble";
import { chatScrollAreaStyle } from "@/lib/chat/layout";
import { mcColors, mcButtonSecondaryStyle } from "@/lib/missionControl/layout";
import type { CachedMessage } from "@/lib/chat/lanes";

type Props = {
  messages: CachedMessage[];
  sending: boolean;
  err: string;
  liveUpdatesStatus: string;
  showJumpToLatest: boolean;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onScroll: () => void;
  onJumpToLatest: () => void;
};

export function ChatTimeline({
  messages,
  sending,
  err,
  liveUpdatesStatus,
  showJumpToLatest,
  scrollContainerRef,
  messagesEndRef,
  onScroll,
  onJumpToLatest,
}: Props) {
  return (
    <>
      <div ref={scrollContainerRef} onScroll={onScroll} style={chatScrollAreaStyle} data-chat-scroll-main>
        {liveUpdatesStatus ? (
          <p style={{ color: mcColors.textMuted, fontSize: 12, marginBottom: 12 }} role="status">
            {liveUpdatesStatus}
          </p>
        ) : null}

        {err ? (
          <p style={{ color: mcColors.red, fontSize: 13, marginBottom: 12 }} role="alert">
            {err}
          </p>
        ) : null}

        <div style={{ display: "flex", flexDirection: "column", gap: 14, width: "100%" }}>
          {messages.map((m) => (
            <ChatMessageBubble
              key={m.id}
              message={m}
              streaming={sending && m.role === "assistant" && !m.content}
            />
          ))}
          <div ref={messagesEndRef} aria-hidden style={{ height: 1 }} />
        </div>
      </div>

      {showJumpToLatest ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "0 28px 8px" }}>
          <button type="button" onClick={onJumpToLatest} style={mcButtonSecondaryStyle}>
            Jump to latest
          </button>
        </div>
      ) : null}
    </>
  );
}
