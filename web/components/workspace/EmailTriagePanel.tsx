"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  createDraft,
  listDrafts,
  sendDraftPreflight,
  triageInbox,
  type EmailDraft,
  type TriagedMessage,
} from "@/lib/workspace/emailApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";

const PROVIDERS_EMAIL_IMAP_HREF = missionControlHref("providers");

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${mcColors.border}`,
  background: "rgba(0,0,0,0.3)",
  color: mcColors.text,
  fontSize: 13,
} as const;

export function EmailTriagePanel() {
  const [messages, setMessages] = useState<TriagedMessage[]>([]);
  const [drafts, setDrafts] = useState<EmailDraft[]>([]);
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [draftBody, setDraftBody] = useState("");

  const refresh = useCallback(async () => {
    const [t, d] = await Promise.all([triageInbox(), listDrafts()]);
    if (!t.ok) setError(t.error === "imap_not_configured" ? "imap_not_configured" : t.error || "load_failed");
    else setError(null);
    if (t.hint) setInfo(t.hint);
    setMessages(t.messages || []);
    setDrafts(d.drafts || []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitDraft = useCallback(async () => {
    if (!to.trim() || !draftBody.trim()) return;
    const res = await createDraft({ to: to.trim(), subject: subject.trim(), body: draftBody.trim() });
    if (res.ok) {
      setTo("");
      setSubject("");
      setDraftBody("");
      setInfo("Draft saved — nothing was sent.");
      await refresh();
    } else {
      setError(res.error || "draft_failed");
    }
  }, [to, subject, draftBody, refresh]);

  const imapNotConfigured = error === "imap_not_configured";

  const requestSend = useCallback(async (draftId: string) => {
    const res = await sendDraftPreflight(draftId);
    setInfo(
      res.ok
        ? "Outbound preflight created — approve in Mission Control to actually send."
        : `Send preflight failed: ${res.error}`,
    );
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS · WORKSPACE</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>
              Email <span className="aethos-governance-chip">drafts only · send needs approval</span>
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              Readonly IMAP triage (urgency, tags, summary, spam). Connect your inbox in{" "}
              <Link href={PROVIDERS_EMAIL_IMAP_HREF} style={{ color: mcColors.cyan }}>
                Providers → Email (IMAP/SMTP)
              </Link>
              . Replies are <strong>drafts only</strong> — sending routes through a governed outbound preflight you
              approve in Mission Control.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link href="/" style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              ← Chat
            </Link>
            <Link href={missionControlHref("home")} style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              Mission Control
            </Link>
          </div>
        </div>

        <WorkspaceNav active="email" />

        {imapNotConfigured ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 16 }}>
            <p style={{ margin: "0 0 10px", fontSize: 13, color: mcColors.textMuted }}>
              Connect your inbox to triage mail — vault-backed and scoped to your account. Draft replies work without
              IMAP.
            </p>
            <Link
              href={PROVIDERS_EMAIL_IMAP_HREF}
              style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12, display: "inline-block" }}
            >
              Connect in Providers → Email (IMAP/SMTP)
            </Link>
          </section>
        ) : null}

        {error && !imapNotConfigured ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, borderColor: "color-mix(in srgb, var(--aethos-danger) 45%, transparent)" }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-danger)" }}>
              {error === "workspace_suite_disabled"
                ? "The workspace suite is turned off for this deployment. Ask AethOS in chat how to enable it."
                : `Error: ${error}`}
            </p>
          </section>
        ) : null}

        {info ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.cyan }}>{info}</p>
          </section>
        ) : null}

        <section style={{ ...mcPanelSectionStyle, marginBottom: 16 }}>
          <h2 style={{ margin: "0 0 10px", fontSize: 14 }}>Inbox ({messages.length})</h2>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            {messages.map((m) => (
              <li key={m.uid} style={{ padding: "10px 12px", borderRadius: 8, border: `1px solid ${mcColors.border}`, background: "rgba(0,0,0,0.2)" }}>
                <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                  {m.urgency === "high" ? <span style={{ fontSize: 11, color: "var(--aethos-danger)", fontWeight: 700 }}>URGENT</span> : null}
                  {m.spam ? <span style={{ fontSize: 11, color: "var(--aethos-warn)" }}>spam?</span> : null}
                  <span style={{ fontSize: 13, fontWeight: 600, flex: 1 }}>{m.subject || "(no subject)"}</span>
                  <button type="button" onClick={() => { setTo(m.from); setSubject(`Re: ${m.subject}`); }} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
                    Draft reply
                  </button>
                </div>
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 2 }}>{m.from}</div>
                <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>{m.snippet}</div>
                {m.tags.length ? (
                  <div style={{ marginTop: 6, display: "flex", gap: 6 }}>
                    {m.tags.map((tag) => (
                      <span key={tag} style={{ fontSize: 10, padding: "2px 8px", borderRadius: 999, background: "rgba(34,211,238,0.1)", color: mcColors.cyan }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
            {messages.length === 0 ? (
              <li style={{ fontSize: 12, color: mcColors.textMuted }}>
                {imapNotConfigured
                  ? "No inbox yet — connect IMAP in Providers to triage mail."
                  : "No messages in this mailbox."}
              </li>
            ) : null}
          </ul>
        </section>

        <section style={mcPanelSectionStyle}>
          <h2 style={{ margin: "0 0 10px", fontSize: 14 }}>Draft reply</h2>
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="To" style={{ ...inputStyle, flex: 1 }} />
            <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject" style={{ ...inputStyle, flex: 1 }} />
          </div>
          <textarea
            value={draftBody}
            onChange={(e) => setDraftBody(e.target.value)}
            placeholder="Write a reply… (draft only — never auto-sent)"
            style={{ ...inputStyle, width: "100%", minHeight: 120, resize: "vertical", marginBottom: 8 }}
          />
          <button type="button" onClick={() => void submitDraft()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
            Save draft
          </button>

          <ul style={{ listStyle: "none", margin: "12px 0 0", padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            {drafts.map((d) => (
              <li key={d.id} style={{ padding: "8px 10px", borderRadius: 8, border: `1px solid ${mcColors.border}`, background: "rgba(0,0,0,0.2)", display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ flex: 1, fontSize: 12 }}>
                  <span style={{ color: mcColors.textDim }}>to {d.to}</span> — {d.subject || "(no subject)"}
                </div>
                <span style={{ fontSize: 11, color: d.sent ? "var(--aethos-ok)" : mcColors.textDim }}>{d.status}</span>
                <button type="button" onClick={() => void requestSend(d.id)} style={{ ...mcButtonSecondaryStyle, fontSize: 11 }}>
                  Send… (governed)
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
