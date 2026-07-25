"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type Command = {
  id: string;
  label: string;
  hint?: string;
  href: string;
  keywords?: string;
};

const COMMANDS: Command[] = [
  { id: "chat", label: "Chat", hint: "Conversation", href: "/", keywords: "home talk ask" },
  { id: "mission-control", label: "Mission Control", hint: "Governance · approvals · agents", href: "/mission-control", keywords: "jobs approvals governance orchestration" },
  { id: "canvas", label: "Live Canvas", hint: "Visual surface", href: "/canvas", keywords: "draw visual" },
  { id: "skills", label: "Skills", hint: "Per-agent skills", href: "/skills", keywords: "abilities tools" },
  { id: "ws-docs", label: "Workspace · Documents", hint: "Docs", href: "/workspace/documents", keywords: "files docs" },
  { id: "ws-notes", label: "Workspace · Notes & Tasks", hint: "Notes", href: "/workspace/notes", keywords: "todo tasks notes" },
  { id: "ws-calendar", label: "Workspace · Calendar", hint: "Calendar", href: "/workspace/calendar", keywords: "events schedule" },
  { id: "ws-email", label: "Workspace · Email", hint: "Email triage", href: "/workspace/email", keywords: "mail inbox" },
  { id: "ws-foundry", label: "Workspace · Model Foundry", hint: "Local models", href: "/workspace/foundry", keywords: "models llm local" },
];

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.45)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  paddingTop: "12vh",
  zIndex: 1000,
};

const panelStyle: React.CSSProperties = {
  width: "100%",
  maxWidth: 520,
  background: "var(--aethos-surface-strong)",
  backdropFilter: "blur(12px)",
  border: "1px solid var(--aethos-border)",
  borderRadius: 14,
  boxShadow: "0 24px 64px rgba(0,0,0,0.5)",
  overflow: "hidden",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  padding: "14px 16px",
  border: "none",
  borderBottom: "1px solid var(--aethos-border)",
  background: "transparent",
  color: "var(--aethos-text)",
  fontSize: 15,
  outline: "none",
};

function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName.toLowerCase();
  return tag === "input" || tag === "textarea" || el.isContentEditable;
}

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COMMANDS;
    return COMMANDS.filter((c) =>
      `${c.label} ${c.hint ?? ""} ${c.keywords ?? ""}`.toLowerCase().includes(q),
    );
  }, [query]);

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setCursor(0);
  }, []);

  const run = useCallback(
    (cmd: Command | undefined) => {
      if (!cmd) return;
      close();
      router.push(cmd.href);
    },
    [close, router],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const cmdK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k";
      const slash = e.key === "/" && !isTypingTarget(e.target);
      if (cmdK || slash) {
        e.preventDefault();
        setOpen((v) => !v);
        return;
      }
      if (e.key === "Escape" && open) {
        e.preventDefault();
        close();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  useEffect(() => {
    if (open) {
      setCursor(0);
      const id = window.setTimeout(() => inputRef.current?.focus(), 20);
      return () => window.clearTimeout(id);
    }
  }, [open]);

  if (!open) return null;

  return (
    <div
      style={overlayStyle}
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div style={panelStyle} role="dialog" aria-label="Command palette" aria-modal="true">
        <input
          ref={inputRef}
          style={inputStyle}
          placeholder="Jump to… (type to filter, ↑↓ to move, ↵ to open)"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setCursor(0);
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setCursor((c) => Math.min(c + 1, results.length - 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setCursor((c) => Math.max(c - 1, 0));
            } else if (e.key === "Enter") {
              e.preventDefault();
              run(results[cursor]);
            }
          }}
        />
        <ul style={{ listStyle: "none", margin: 0, padding: 6, maxHeight: "50vh", overflowY: "auto" }}>
          {results.length === 0 ? (
            <li style={{ padding: "12px 14px", color: "var(--aethos-text-dim)", fontSize: 13 }}>
              No matches.
            </li>
          ) : (
            results.map((cmd, idx) => {
              const active = idx === cursor;
              return (
                <li key={cmd.id}>
                  <button
                    type="button"
                    onMouseEnter={() => setCursor(idx)}
                    onClick={() => run(cmd)}
                    style={{
                      display: "flex",
                      width: "100%",
                      alignItems: "baseline",
                      gap: 10,
                      padding: "10px 12px",
                      border: "none",
                      borderRadius: 8,
                      background: active ? "var(--aethos-accent-soft)" : "transparent",
                      color: "var(--aethos-text)",
                      cursor: "pointer",
                      textAlign: "left",
                      fontSize: 14,
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{cmd.label}</span>
                    {cmd.hint ? (
                      <span style={{ fontSize: 12, color: "var(--aethos-text-dim)" }}>{cmd.hint}</span>
                    ) : null}
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </div>
    </div>
  );
}
