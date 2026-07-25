"use client";

import Link from "next/link";

import { buildResearchReplayUrl, missionControlHref } from "@/lib/missionControl/deepLinks";
import { mcAlpha, mcColors } from "@/lib/missionControl/layout";
import { apiBase } from "@/lib/api";

type Props = {
  meta: Record<string, unknown>;
};

const badgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: "0.04em",
  textTransform: "uppercase" as const,
  padding: "3px 8px",
  borderRadius: 999,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.25)",
  textDecoration: "none",
  color: mcColors.textMuted,
};

export function ChatAgentMetaBadges({ meta }: Props) {
  const replayId = meta.research_replay_id ? String(meta.research_replay_id) : "";
  const lane = meta.lane ?? meta.route_id;
  const toolCalls = meta.agent_tool_calls;
  const comparisonUrl = meta.comparison_html_url ? String(meta.comparison_html_url) : "";
  const fellBack = String(meta.tool_fallback ?? "") === "true";
  const actualModel = meta.effective_model ? String(meta.effective_model) : "";
  const selectedModel = meta.selected_model_label
    ? String(meta.selected_model_label)
    : meta.selected_model
      ? String(meta.selected_model)
      : "";

  if (!replayId && !lane && !toolCalls && !comparisonUrl && !fellBack) return null;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
      {replayId ? (
        <Link href={buildResearchReplayUrl(replayId)} style={{ ...badgeStyle, color: mcColors.cyan, borderColor: mcAlpha(mcColors.cyan, 27) }}>
          Research · {replayId.slice(0, 12)}
          {replayId.length > 12 ? "…" : ""}
        </Link>
      ) : null}
      {lane ? (
        <Link href={missionControlHref("agents")} style={badgeStyle}>
          {String(lane)}
        </Link>
      ) : null}
      {toolCalls ? (
        <span style={{ ...badgeStyle, cursor: "default" }}>{String(toolCalls)} tools</span>
      ) : null}
      {fellBack && actualModel ? (
        <span
          style={{ ...badgeStyle, cursor: "default", color: "var(--aethos-warn)", borderColor: "color-mix(in srgb, var(--aethos-warn) 27%, transparent)" }}
          title={selectedModel ? `${selectedModel} can't run tools here; tools ran on the cloud fallback.` : undefined}
        >
          {selectedModel ? `${selectedModel} → ` : ""}ran on {actualModel}
        </span>
      ) : null}
      {comparisonUrl ? (
        <a
          href={comparisonUrl.startsWith("http") ? comparisonUrl : `${apiBase()}${comparisonUrl}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{ ...badgeStyle, color: mcColors.cyan, borderColor: mcAlpha(mcColors.cyan, 27) }}
        >
          Comparison page
        </a>
      ) : null}
    </div>
  );
}
