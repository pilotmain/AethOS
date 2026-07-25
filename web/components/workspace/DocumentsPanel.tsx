"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  createDocument,
  deleteDocument,
  getDocument,
  listDocuments,
  updateDocument,
  type DocumentSummary,
  type WorkspaceDocFormat,
  type WorkspaceDocument,
} from "@/lib/workspace/documentsApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";

const FORMATS: WorkspaceDocFormat[] = ["markdown", "text", "csv", "html"];

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${mcColors.border}`,
  background: "rgba(0,0,0,0.3)",
  color: mcColors.text,
  fontSize: 13,
} as const;

export function DocumentsPanel() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<WorkspaceDocument | null>(null);
  const [title, setTitle] = useState("Untitled");
  const [content, setContent] = useState("");
  const [format, setFormat] = useState<WorkspaceDocFormat>("markdown");
  const [dirty, setDirty] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    const res = await listDocuments();
    if (!res.ok) setError(res.error || "load_failed");
    else {
      setError(null);
      setDocs(res.documents);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const openDoc = useCallback(async (id: string) => {
    const res = await getDocument(id);
    if (res.ok && res.document) {
      setActive(res.document);
      setTitle(res.document.title);
      setContent(res.document.content);
      setFormat(res.document.format);
      setDirty(false);
    } else {
      setError(res.error || "open_failed");
    }
  }, []);

  const newDoc = useCallback(() => {
    setActive(null);
    setTitle("Untitled");
    setContent("");
    setFormat("markdown");
    setDirty(true);
  }, []);

  const save = useCallback(async () => {
    if (active) {
      const res = await updateDocument(active.id, { title, content, format });
      if (!res.ok) return setError(res.error || "save_failed");
    } else {
      const res = await createDocument({ title, content, format });
      if (!res.ok) return setError(res.error || "save_failed");
      if (res.document) await openDoc(res.document.id);
    }
    setDirty(false);
    await refresh();
  }, [active, title, content, format, openDoc, refresh]);

  const remove = useCallback(
    async (id: string) => {
      await deleteDocument(id);
      if (active?.id === id) newDoc();
      await refresh();
    },
    [active, newDoc, refresh],
  );

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS · WORKSPACE</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>
              <span className="aethos-gradient-text">Documents</span>{" "}
              <span className="aethos-governance-chip" data-state="readonly">draft-only · no auto-publish</span>
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
              Draft-only local editor. Your drafts stay on your machine and are{" "}
              <strong>never auto-published or sent</strong>.
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

        <WorkspaceNav active="documents" />

        {error ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, borderColor: "color-mix(in srgb, var(--aethos-danger) 45%, transparent)" }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-danger)" }}>
              {error === "workspace_suite_disabled"
                ? "The workspace suite is turned off for this deployment. Ask AethOS in chat how to enable it."
                : `Error: ${error}`}
            </p>
          </section>
        ) : null}

        <div style={{ display: "grid", gridTemplateColumns: "minmax(220px, 300px) 1fr", gap: 16 }}>
          <section style={mcPanelSectionStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <h2 style={{ margin: 0, fontSize: 14 }}>Drafts</h2>
              <button type="button" onClick={newDoc} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
                + New
              </button>
            </div>
            {loading ? <p style={{ fontSize: 12, color: mcColors.textMuted }}>Loading…</p> : null}
            {!loading && docs.length === 0 ? (
              <p style={{ fontSize: 12, color: mcColors.textMuted }}>No drafts yet.</p>
            ) : null}
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
              {docs.map((d) => (
                <li
                  key={d.id}
                  style={{
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: `1px solid ${active?.id === d.id ? mcColors.cyan : mcColors.border}`,
                    background: active?.id === d.id ? "rgba(34,211,238,0.08)" : "rgba(0,0,0,0.2)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <button
                    type="button"
                    onClick={() => void openDoc(d.id)}
                    style={{ background: "none", border: "none", color: mcColors.text, cursor: "pointer", textAlign: "left", flex: 1, fontSize: 13 }}
                  >
                    <div style={{ fontWeight: 600 }}>{d.title}</div>
                    <div style={{ fontSize: 11, color: mcColors.textDim }}>
                      {d.format} · {d.char_count ?? 0} chars
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void remove(d.id)}
                    aria-label={`Delete ${d.title}`}
                    style={{ background: "none", border: "none", color: mcColors.textDim, cursor: "pointer", fontSize: 14 }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section style={mcPanelSectionStyle}>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <input
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setDirty(true);
                }}
                placeholder="Document title"
                style={{ ...inputStyle, flex: 1 }}
              />
              <select
                value={format}
                onChange={(e) => {
                  setFormat(e.target.value as WorkspaceDocFormat);
                  setDirty(true);
                }}
                style={inputStyle}
              >
                {FORMATS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void save()}
                disabled={!dirty}
                style={{ ...mcButtonSecondaryStyle, fontSize: 12, opacity: dirty ? 1 : 0.5 }}
              >
                {active ? "Save" : "Create"}
              </button>
            </div>
            <textarea
              value={content}
              onChange={(e) => {
                setContent(e.target.value);
                setDirty(true);
              }}
              placeholder="Start writing… (draft only — nothing is published)"
              spellCheck
              style={{
                ...inputStyle,
                width: "100%",
                minHeight: "55vh",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                lineHeight: 1.6,
                resize: "vertical",
              }}
            />
            <div style={{ marginTop: 8, fontSize: 11, color: mcColors.textDim }}>
              {content.length} chars · draft-only · {dirty ? "unsaved changes" : "saved"}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
