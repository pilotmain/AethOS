"use client";

import { useMemo } from "react";

import {
  browserArtifactFileUrl,
  type BrowserEvidenceArtifact,
  type BrowserEvidenceAuditEvent,
} from "@/lib/missionControl/browserEvidenceApi";
import { mcPanelSectionStyle, mcColors, mcButtonSecondaryStyle } from "@/lib/missionControl/layout";

type Props = {
  artifacts: BrowserEvidenceArtifact[];
  auditEvents: BrowserEvidenceAuditEvent[];
  onRefresh: () => void;
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

export function BrowserEvidencePanel({ artifacts, auditEvents, onRefresh }: Props) {
  const screenshots = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "browser_screenshot"),
    [artifacts],
  );
  const resolutionArtifacts = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "deployment_url_resolution"),
    [artifacts],
  );
  const metadataOnly = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "deployment_metadata_only"),
    [artifacts],
  );
  const denials = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "browser_policy_denial"),
    [artifacts],
  );

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Browser Evidence</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed screenshot and metadata artifacts — read-only capture, auditable pipeline.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {resolutionArtifacts.length > 0 && (
        <div style={{ marginTop: 12, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          <div style={{ color: "var(--aethos-text)", fontWeight: 600, marginBottom: 6 }}>URL resolution</div>
          {resolutionArtifacts.slice(0, 5).map((art) => {
            const resolution = (art.metadata as { resolution?: Record<string, unknown> } | undefined)?.resolution
              ?? (art as { resolution?: Record<string, unknown> }).resolution;
            const resolved = Boolean(resolution?.resolved);
            return (
              <div key={art.artifact_id} style={{ marginBottom: 8, padding: 8, borderRadius: 8, background: "rgba(0,0,0,0.15)" }}>
                <div>Target: {String(resolution?.target ?? art.source_url ?? "—")}</div>
                {resolved ? (
                  <>
                    <div>Resolved URL: {String(resolution?.public_url ?? "—")}</div>
                    <div>Resolution source: {String(resolution?.resolution_source ?? "—")}</div>
                  </>
                ) : (
                  <div style={{ color: "var(--aethos-warn)" }}>
                    Browser capture skipped: {String(resolution?.failure_reason ?? "no public URL")}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {metadataOnly.length > 0 && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 12, marginTop: 8 }}>
          Metadata-only fallback captured for {metadataOnly.length} deployment target(s) — no browser navigation.
        </p>
      )}

      {screenshots.length === 0 && artifacts.length === 0 ? (
        <p style={{ color: "var(--aethos-text-dim)", fontSize: 13, marginTop: 12 }}>No browser evidence artifacts yet.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: 12,
            marginTop: 12,
          }}
        >
          {screenshots.map((art) => (
            <article
              key={art.artifact_id}
              style={{
                borderRadius: 10,
                border: "1px solid rgba(255,255,255,0.08)",
                overflow: "hidden",
                background: "rgba(0,0,0,0.2)",
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={browserArtifactFileUrl(art.artifact_id)}
                alt={`Screenshot ${art.source_url ?? art.artifact_id}`}
                style={{ width: "100%", height: 140, objectFit: "cover", display: "block", background: "var(--aethos-bg-card)" }}
              />
              <div style={{ padding: 10, fontSize: 11, lineHeight: 1.45 }}>
                <div style={{ color: "var(--aethos-text)", fontWeight: 600 }}>{art.capture_type ?? "screenshot"}</div>
                <div style={{ color: "var(--aethos-text-muted)", wordBreak: "break-all" }}>{art.source_url ?? "—"}</div>
                <div style={{ color: "var(--aethos-text-dim)", marginTop: 4 }}>{formatTs(art.created_at)}</div>
                {art.file_exists === false || (art.file_size_bytes ?? 0) <= 0 ? (
                  <div style={{ color: "var(--aethos-danger)", marginTop: 6 }}>File missing — capture did not produce a readable artifact.</div>
                ) : (
                  <a
                    href={browserArtifactFileUrl(art.artifact_id)}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "var(--aethos-accent)", display: "inline-block", marginTop: 6 }}
                  >
                    Open full artifact
                  </a>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      <details style={{ marginTop: 16 }}>
        <summary style={{ cursor: "pointer", fontSize: 13, color: "var(--aethos-text)" }}>Evidence chain ({artifacts.length})</summary>
        <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          {artifacts.slice(0, 20).map((art) => (
            <li key={art.artifact_id}>
              <code>{art.artifact_id}</code> · {art.artifact_type} · {art.source_url ?? "—"} · tier {art.risk_tier ?? "—"}
            </li>
          ))}
        </ul>
      </details>

      <details style={{ marginTop: 12 }}>
        <summary style={{ cursor: "pointer", fontSize: 13, color: "var(--aethos-text)" }}>Browser timeline</summary>
        <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          {auditEvents.slice(0, 15).map((ev, idx) => (
            <li key={`${ev.at}-${idx}`}>
              {formatTs(ev.at)} · {ev.action} · {ev.result} · {ev.target_url ?? "—"}
            </li>
          ))}
          {auditEvents.length === 0 && <li>No audit events yet.</li>}
        </ul>
      </details>

      <details style={{ marginTop: 12 }}>
        <summary style={{ cursor: "pointer", fontSize: 13, color: "var(--aethos-text)" }}>Browser diagnostics</summary>
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          <p style={{ margin: "0 0 6px" }}>Policy denials: {denials.length}</p>
          {denials.slice(0, 5).map((d) => (
            <div key={d.artifact_id} style={{ marginBottom: 4 }}>
              <code>{d.artifact_id}</code> · {String((d as { detail?: string }).detail ?? "blocked")}
            </div>
          ))}
          <p style={{ margin: "8px 0 0" }}>
            Console/network metadata stored as separate artifacts in the evidence chain.
          </p>
        </div>
      </details>
    </section>
  );
}
