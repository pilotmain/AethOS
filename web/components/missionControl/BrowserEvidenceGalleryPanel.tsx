"use client";

import {
  browserArtifactFileUrl,
  type BrowserEvidenceArtifact,
} from "@/lib/missionControl/browserEvidenceApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type Props = {
  artifacts: BrowserEvidenceArtifact[];
  onRefresh: () => void;
};

export function BrowserEvidenceGalleryPanel({ artifacts, onRefresh }: Props) {
  const screenshots = artifacts.filter((a) => a.artifact_type === "browser_screenshot");

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Gallery</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
            Visual browser evidence — governed screenshots from automation runs.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>
      {screenshots.length === 0 ? (
        <p style={{ marginTop: 16, fontSize: 13, color: mcColors.textMuted }}>No screenshots yet.</p>
      ) : (
        <div
          style={{
            marginTop: 16,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 12,
          }}
        >
          {screenshots.slice(0, 24).map((art) => (
            <a
              key={art.artifact_id}
              href={browserArtifactFileUrl(art.artifact_id)}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "block",
                borderRadius: 12,
                overflow: "hidden",
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.25)",
                textDecoration: "none",
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={browserArtifactFileUrl(art.artifact_id)}
                alt={art.source_url || art.artifact_id}
                style={{ width: "100%", height: 140, objectFit: "cover", display: "block" }}
              />
              <div style={{ padding: 8, fontSize: 10, color: mcColors.textMuted }}>
                {(art.source_url || art.artifact_id || "").slice(0, 60)}
              </div>
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
