"use client";

import { useState } from "react";

import { formatBrowserProfileSaveError } from "@/lib/missionControl/browserProfileErrors";
import { saveBrowserProfile, type PersistenceMode } from "@/lib/missionControl/browserProfiles";
import type { BrowserSessionRecord } from "@/lib/missionControl/browserSessions";

type Props = {
  session: BrowserSessionRecord;
  onSaved: () => void;
  onDismiss: () => void;
};

type SaveState = "idle" | "saving" | "saved" | "failed";

const PERSISTENCE_OPTIONS: { value: PersistenceMode; label: string }[] = [
  { value: "use_once", label: "Use once only" },
  { value: "persistent", label: "Save until I remove it" },
  { value: "expires_7d", label: "Save for 7 days" },
  { value: "expires_30d", label: "Save for 30 days" },
];

export function shouldShowSaveBrowserSessionPrompt(session: BrowserSessionRecord): boolean {
  return Boolean(session.profile_save_eligible);
}

export function SaveBrowserSessionPrompt({ session, onSaved, onDismiss }: Props) {
  const [state, setState] = useState<SaveState>("idle");
  const [error, setError] = useState("");
  const [mode, setMode] = useState<PersistenceMode>("use_once");

  if (!shouldShowSaveBrowserSessionPrompt(session)) {
    return null;
  }

  const runSave = async (persistenceMode: PersistenceMode) => {
    if (state === "saving" || state === "saved") {
      return;
    }
    setState("saving");
    setError("");
    try {
      await saveBrowserProfile(session.id, persistenceMode);
      setState("saved");
      onSaved();
    } catch (e) {
      setState("failed");
      setError(formatBrowserProfileSaveError(e));
    }
  };

  const persistenceHint =
    session.persistence_last_error != null
      ? `Last attempt: ${session.persistence_last_error}`
      : session.storage_state_available
        ? "Storage state: available"
        : "Storage state: not ready";

  return (
    <div
      style={{
        marginTop: 12,
        padding: 12,
        borderRadius: 12,
        border: "1px solid rgba(96,165,250,0.35)",
        background: "rgba(59,130,246,0.08)",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        {state === "saved"
          ? "✓ Session saved for future read-only checks"
          : "How should AethOS remember this session?"}
      </div>
      <p style={{ margin: "0 0 6px", color: "var(--aethos-text-muted)", fontSize: 12, lineHeight: 1.45 }}>
        Default is <strong>use once only</strong>. Saved sessions store browser state locally for{" "}
        <strong>{session.target}</strong> — not your password.
      </p>
      <p style={{ margin: "0 0 8px", color: "var(--aethos-text-dim)", fontSize: 11 }}>
        {persistenceHint}
        {session.persistence_status && session.persistence_status !== "none"
          ? ` · status: ${session.persistence_status}`
          : ""}
      </p>
      {state !== "saved" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
          {PERSISTENCE_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer" }}
            >
              <input
                type="radio"
                name={`persist-${session.id}`}
                value={opt.value}
                checked={mode === opt.value}
                onChange={() => setMode(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      )}
      {error && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 12, marginBottom: 8 }} role="status">
          {error}
        </p>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {state !== "saved" && (
          <button
            type="button"
            disabled={state === "saving"}
            onClick={() => void runSave(mode)}
            style={{
              borderRadius: 8,
              padding: "6px 12px",
              fontSize: 12,
              fontWeight: 600,
              cursor: state === "saving" ? "wait" : "pointer",
              border: "1px solid rgba(96,165,250,0.4)",
              background: "rgba(59,130,246,0.15)",
              color: "var(--aethos-accent)",
            }}
          >
            {state === "saving"
              ? "Saving session…"
              : state === "failed"
                ? "Retry save"
                : "Save with selected option"}
          </button>
        )}
        {state !== "saved" && (
          <button
            type="button"
            disabled={state === "saving"}
            onClick={onDismiss}
            style={{
              borderRadius: 8,
              padding: "6px 12px",
              fontSize: 12,
              cursor: "pointer",
              border: "1px solid rgba(255,255,255,0.15)",
              background: "transparent",
              color: "var(--aethos-text-muted)",
            }}
          >
            Dismiss (use once only)
          </button>
        )}
      </div>
    </div>
  );
}
