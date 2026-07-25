"use client";

import { useMemo } from "react";

import { type ResearchArtifact } from "@/lib/missionControl/researchApi";
import { mcPanelSectionStyle, mcColors, mcButtonSecondaryStyle } from "@/lib/missionControl/layout";

type Props = {
  artifacts: ResearchArtifact[];
  onRefresh: () => void;
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

export function WebIntelligencePanel({ artifacts, onRefresh }: Props) {
  const inspections = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "website_metadata_summary"),
    [artifacts],
  );
  const searches = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "web_search_result_set"),
    [artifacts],
  );
  const denials = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "research_policy_denial"),
    [artifacts],
  );

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Research / Web Intelligence</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed website inspections, search attempts, and policy denials — evidence-first, no hidden browsing.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {artifacts.length === 0 ? (
        <p style={{ marginTop: 16, color: mcColors.textMuted, fontSize: 13 }}>
          No web intelligence artifacts yet. Try: &quot;Can you tell me high level details about pilotmain.com&quot;
        </p>
      ) : (
        <>
          {inspections.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Website inspections</h3>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
                {inspections.slice(0, 20).map((art) => {
                  const payload = art.payload ?? {};
                  const meta = (payload.metadata as Record<string, unknown> | undefined) ?? {};
                  const err = payload.error as string | undefined;
                  return (
                    <li
                      key={art.artifact_id}
                      style={{
                        padding: "10px 12px",
                        marginBottom: 8,
                        borderRadius: 10,
                        background: "rgba(0,0,0,0.15)",
                        border: "1px solid rgba(255,255,255,0.06)",
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>{art.source_url ?? "—"}</div>
                      <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                        {err ? (
                          <span style={{ color: "var(--aethos-warn)" }}>Error: {err}</span>
                        ) : (
                          <>
                            Title: {String(meta.title ?? "—")} · Confidence: {art.confidence ?? "—"} · Channel:{" "}
                            {art.channel ?? "—"}
                          </>
                        )}
                      </div>
                      <div style={{ color: mcColors.textMuted, marginTop: 4, fontSize: 12 }}>
                        {formatTs(art.created_at)} · {art.artifact_id} · {art.evidence_source ?? "—"}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {searches.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Web search</h3>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
                {searches.slice(0, 10).map((art) => (
                  <li
                    key={art.artifact_id}
                    style={{ padding: "8px 12px", marginBottom: 6, borderRadius: 8, background: "rgba(0,0,0,0.12)" }}
                  >
                    Query: {String((art.payload as { query?: string })?.query ?? "—")} ·{" "}
                    {(art.payload as { configured?: boolean })?.configured === false ? "not configured" : "attempted"} ·{" "}
                    {art.artifact_id}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {denials.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Policy denials</h3>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
                {denials.slice(0, 10).map((art) => (
                  <li key={art.artifact_id} style={{ padding: "8px 12px", marginBottom: 6, color: "var(--aethos-danger)" }}>
                    {String((art.payload as { reason?: string })?.reason ?? "denied")} · {art.artifact_id}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
