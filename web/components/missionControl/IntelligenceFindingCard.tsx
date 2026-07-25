"use client";

import type { IntelligenceFinding } from "@/lib/missionControl/intelligenceFinding";
import { formatConfidence, sectionLabel } from "@/lib/missionControl/intelligenceFinding";
import { mcColors } from "@/lib/missionControl/layout";

type Props = {
  finding: IntelligenceFinding;
  compact?: boolean;
};

const severityColor = (sev?: IntelligenceFinding["severity"]) => {
  if (sev === "high") return mcColors.red;
  if (sev === "medium") return mcColors.amber;
  if (sev === "low") return mcColors.cyan;
  return mcColors.textDim;
};

const sectionStyle = {
  marginTop: 12,
} as const;

const labelStyle = {
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: mcColors.textDim,
  marginBottom: 6,
};

const bodyStyle = {
  fontSize: 13,
  color: mcColors.textMuted,
  lineHeight: 1.55,
  margin: 0,
};

export function IntelligenceFindingCard({ finding, compact = false }: Props) {
  return (
    <article
      style={{
        padding: compact ? "12px 14px" : "16px 18px",
        marginBottom: 12,
        borderRadius: 10,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.2)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
        <h3 style={{ margin: 0, fontSize: compact ? 14 : 15, fontWeight: 600, color: mcColors.text, lineHeight: 1.4 }}>
          {sectionLabel.finding}: {finding.finding}
        </h3>
        {finding.severity ? (
          <span style={{ fontSize: 10, fontWeight: 600, color: severityColor(finding.severity), whiteSpace: "nowrap" }}>
            {finding.severity.toUpperCase()}
          </span>
        ) : null}
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>{sectionLabel.evidence}</div>
        <ul style={{ ...bodyStyle, paddingLeft: 18, margin: 0 }}>
          {finding.evidence.map((line) => (
            <li key={line} style={{ marginBottom: 4 }}>
              {line}
            </li>
          ))}
        </ul>
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>{sectionLabel.confidence}</div>
        <p style={bodyStyle}>
          {formatConfidence(finding.confidence)}
          {finding.confidenceReason ? (
            <>
              {" — "}
              {finding.confidenceReason}
            </>
          ) : null}
        </p>
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>{sectionLabel.impact}</div>
        <p style={bodyStyle}>{finding.impact}</p>
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>{sectionLabel.recommendedReview}</div>
        <ul style={{ ...bodyStyle, paddingLeft: 18, margin: 0 }}>
          {finding.recommendedReview.map((line) => (
            <li key={line} style={{ marginBottom: 4 }}>
              {line}
            </li>
          ))}
        </ul>
      </div>

      {finding.companionCommentary ? (
        <details style={{ ...sectionStyle, marginTop: 14 }}>
          <summary style={{ ...labelStyle, cursor: "pointer", listStyle: "none" }}>
            {sectionLabel.companionCommentary} (optional)
          </summary>
          <p style={{ ...bodyStyle, marginTop: 8, fontStyle: "italic", opacity: 0.85 }}>{finding.companionCommentary}</p>
        </details>
      ) : null}
    </article>
  );
}
