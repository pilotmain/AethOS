"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { ChatThread } from "@/lib/chat/chatThreads";
import { AethosLogo } from "@/components/branding/AethosLogo";
import { missionControlHref } from "@/lib/missionControl/deepLinks";
import { mcColors } from "@/lib/missionControl/layout";

type Props = {
  mobileOpen?: boolean;
  /** Desktop collapse (Ctrl/⌘+B). Hides the column unless the mobile overlay is open. */
  collapsed?: boolean;
  onCloseMobile?: () => void;
  threads: ChatThread[];
  activeThreadId: string;
  /** Threads with an in-flight turn — drives the background "working…" hint. */
  busyThreadIds?: string[];
  onSelectThread: (threadId: string) => void;
  onNewChat: () => void;
  onDeleteThread?: (threadId: string) => void;
};

type ToolLink = {
  href: string;
  label: string;
  hint: string;
  external?: boolean;
};

const TOOL_LINKS: ToolLink[] = [
  { href: missionControlHref("research"), label: "Research", hint: "Deep compare & replays" },
  { href: missionControlHref("gallery"), label: "Gallery", hint: "Browser screenshots", external: true },
  { href: missionControlHref("library"), label: "Library", hint: "Saved research replays", external: true },
  { href: missionControlHref("agents"), label: "Agents", hint: "Orchestration threads" },
  { href: missionControlHref("approvals"), label: "Approvals", hint: "Governed execution" },
  { href: missionControlHref("jobs"), label: "Jobs", hint: "Tracked work" },
  { href: "/skills", label: "Skills", hint: "Operator playbooks", external: true },
  { href: missionControlHref("mcp"), label: "MCP", hint: "Tool bridge", external: true },
];

const navBtn = (active?: boolean) =>
  ({
    display: "block",
    width: "100%",
    textAlign: "left" as const,
    padding: "8px 10px",
    marginBottom: 2,
    borderRadius: 10,
    border: "none",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: active ? 600 : 500,
    color: active ? "var(--aethos-text-strong)" : mcColors.textMuted,
    background: active ? "rgba(34,211,238,0.12)" : "transparent",
    boxShadow: active ? "inset 3px 0 0 var(--aethos-accent)" : "none",
  }) as const;

export function ChatSidebar({
  mobileOpen,
  collapsed,
  onCloseMobile,
  threads,
  activeThreadId,
  busyThreadIds,
  onSelectThread,
  onNewChat,
  onDeleteThread,
}: Props) {
  const [filter, setFilter] = useState("");
  const [chatsOpen, setChatsOpen] = useState(true);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((t) => t.title.toLowerCase().includes(q));
  }, [filter, threads]);

  return (
    <aside
      className="chat-sidebar mc-sidebar"
      style={{
        width: 240,
        flexShrink: 0,
        // Collapsed hides the desktop column; the mobile overlay (mobileOpen) still wins.
        display: collapsed && !mobileOpen ? "none" : "flex",
        flexDirection: "column",
        borderRight: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.4)",
        backdropFilter: "blur(10px)",
      }}
      data-mobile-open={mobileOpen ? "true" : undefined}
      data-collapsed={collapsed ? "true" : undefined}
    >
      <div style={{ padding: "20px 16px 12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <AethosLogo size={22} />
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>
            AETHOS
          </div>
        </div>
        <div className="aethos-gradient-text" style={{ fontSize: 15, fontWeight: 700, marginTop: 4, width: "fit-content" }}>
          Operator Console
        </div>
      </div>

      <div style={{ padding: "0 12px 10px" }}>
        <input
          type="search"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search chats…"
          aria-label="Search chats"
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "8px 10px",
            borderRadius: 8,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(0,0,0,0.35)",
            color: mcColors.text,
            fontSize: 12,
          }}
        />
      </div>

      <nav style={{ flex: 1, overflowY: "auto", padding: "0 8px 16px" }}>
        <button
          type="button"
          onClick={() => {
            onNewChat();
            onCloseMobile?.();
          }}
          style={{
            ...navBtn(false),
            marginBottom: 10,
            color: mcColors.cyan,
            fontWeight: 600,
          }}
        >
          + New chat
        </button>

        <button
          type="button"
          onClick={() => setChatsOpen((v) => !v)}
          style={{
            ...navBtn(false),
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: mcColors.textDim,
            background: "transparent",
            boxShadow: "none",
          }}
        >
          {chatsOpen ? "▼" : "▶"} Chats ({threads.length})
        </button>

        {chatsOpen
          ? filtered.map((thread) => {
              const active = thread.id === activeThreadId;
              const working = !!busyThreadIds?.includes(thread.id) && !active;
              return (
                <div key={thread.id} style={{ display: "flex", gap: 4, alignItems: "stretch" }}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectThread(thread.id);
                      onCloseMobile?.();
                    }}
                    style={{
                      ...navBtn(active),
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      minHeight: 34,
                      overflow: "hidden",
                    }}
                    title={working ? `${thread.title} — working…` : thread.title}
                  >
                    {working ? (
                      <span
                        aria-hidden="true"
                        style={{
                          flexShrink: 0,
                          width: 7,
                          height: 7,
                          borderRadius: "50%",
                          background: mcColors.cyan,
                          boxShadow: `0 0 6px ${mcColors.cyan}`,
                          animation: "mc-pulse-soft 1.1s ease-in-out infinite",
                        }}
                      />
                    ) : null}
                    <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {thread.title || "New chat"}
                    </span>
                    {working ? (
                      <span style={{ flexShrink: 0, fontSize: 10, color: mcColors.textDim }}>working…</span>
                    ) : null}
                  </button>
                  {onDeleteThread && threads.length > 1 ? (
                    <button
                      type="button"
                      aria-label={`Delete ${thread.title}`}
                      onClick={() => onDeleteThread(thread.id)}
                      style={{
                        border: "none",
                        borderRadius: 8,
                        background: "transparent",
                        color: mcColors.textDim,
                        cursor: "pointer",
                        fontSize: 14,
                        padding: "0 6px",
                      }}
                    >
                      ×
                    </button>
                  ) : null}
                </div>
              );
            })
          : null}

        {chatsOpen && filtered.length === 0 ? (
          <p style={{ margin: "4px 10px 0", fontSize: 12, color: mcColors.textMuted, lineHeight: 1.4 }}>
            {filter.trim() ? "No chats match your search." : "No chats yet — start one above."}
          </p>
        ) : null}

        <div style={{ height: 1, background: mcColors.borderSubtle, margin: "14px 8px" }} />

        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: mcColors.textDim,
            padding: "0 8px 6px",
          }}
        >
          Tools
        </div>
        {TOOL_LINKS.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            onClick={() => onCloseMobile?.()}
            style={{
              display: "block",
              padding: "8px 10px",
              marginBottom: 2,
              borderRadius: 10,
              fontSize: 13,
              fontWeight: 500,
              color: mcColors.textMuted,
              textDecoration: "none",
            }}
            title={link.hint}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <footer
        style={{
          padding: "14px 16px",
          borderTop: `1px solid ${mcColors.borderSubtle}`,
          fontSize: 11,
          color: mcColors.textMuted,
        }}
      >
        <div className="aethos-gradient-text" style={{ fontWeight: 700, width: "fit-content" }}>AethOS Operator</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4, color: mcColors.green }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: mcColors.green,
              boxShadow: `0 0 8px ${mcColors.green}`,
            }}
          />
          Online
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 10 }}>Ctrl+B / ⌘B toggles sidebar</p>
      </footer>
    </aside>
  );
}
