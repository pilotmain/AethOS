"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  appendMissionControlPilotValidationTrustBoardRecord,
  fetchMissionControlPilotValidationTrustBoard,
  type PilotValidationTrustBoardResponse,
} from "@/lib/missionControl/missionControlPilotValidationTrustBoardApi";

type Props = { sessionId?: string };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const trustColor = (value?: string) => {
  if (value === "yes") return mcColors.cyan;
  if (value === "conditional") return mcColors.amber;
  if (value === "no") return mcColors.red;
  return mcColors.textMuted;
};

function sectionRows(board: Record<string, unknown>, key: string): Record<string, unknown>[] {
  const sections = (board.sections as Record<string, unknown[]>) || {};
  const rows = sections[key];
  return Array.isArray(rows) ? (rows as Record<string, unknown>[]) : [];
}

export function PilotValidationTrustBoardPanel({ sessionId = "operator" }: Props) {
  const [data, setData] = useState<PilotValidationTrustBoardResponse | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await fetchMissionControlPilotValidationTrustBoard(sessionId, "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load pilot validation trust board");
    }
  }, [sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  const board = (data?.pilot_validation_trust_board || {}) as Record<string, unknown>;
  const stageSummary = sectionRows(board, "stage_completion_summary")[0] || {};
  const effort = sectionRows(board, "human_effort_scoring")[0] || {};
  const trust = sectionRows(board, "trust_recommendation")[0] || {};
  const approvals = sectionRows(board, "approval_friction_metrics")[0] || {};
  const reengagements = sectionRows(board, "re_engagement_metrics")[0] || {};

  const saveNote = async () => {
    const text = note.trim();
    if (!text) return;
    setBusy(true);
    try {
      await appendMissionControlPilotValidationTrustBoardRecord(sessionId, "validation_artifact", text);
      setNote("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save validation note");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Pilot Validation Trust Board</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            FIX 183 — composes FIX 181 pilot audits only (validation ≠ re-execution).
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      <div style={{ marginTop: 16 }}>
        <div style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
            <span style={{ fontWeight: 600 }}>Trust recommendation</span>
            <span style={{ color: trustColor(String(trust.trust_recommendation || board.trust_recommendation || "unknown")) }}>
              {String(trust.trust_recommendation || board.trust_recommendation || "—")}
            </span>
          </div>
          <div style={{ color: mcColors.textDim, marginTop: 6 }}>
            {String(trust.trust_rationale || data?.detail || "Run FIX 181 pilot harness to populate trust metrics.")}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10 }}>
          <div style={cardStyle}>
            <div style={{ fontSize: 11, color: mcColors.textMuted }}>Human effort score</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: mcColors.cyan }}>
              {String(effort.human_effort_score ?? board.human_effort_score ?? "—")}
            </div>
            <div style={{ fontSize: 11, color: mcColors.textDim }}>{String(effort.human_effort_label || "")}</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 11, color: mcColors.textMuted }}>Approvals</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{String(approvals.approval_count ?? board.approval_count ?? 0)}</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 11, color: mcColors.textMuted }}>Re-engagements</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{String(reengagements.re_engagement_count ?? board.re_engagement_count ?? 0)}</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 11, color: mcColors.textMuted }}>Pilot audits</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{String(board.pilot_audit_count ?? 0)}</div>
          </div>
        </div>

        <div style={cardStyle}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Stage completion</div>
          <div style={{ fontSize: 12, color: mcColors.textDim }}>
            Completed: {JSON.stringify(stageSummary.stages_completed || [])}
          </div>
          <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>
            Pending: {JSON.stringify(stageSummary.stages_pending || [])}
          </div>
          <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>
            Stopped at: {String(stageSummary.stage_stopped_at || "—")} · Outcome: {String(stageSummary.pilot_outcome || board.pilot_outcome || "none")}
          </div>
        </div>

        <div style={cardStyle}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Validation artifact note</div>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="validation artifact: operator observation from manual gate"
            rows={3}
            style={{ width: "100%", fontSize: 12, padding: 8, borderRadius: 8, border: `1px solid ${mcColors.borderSubtle}`, background: "rgba(0,0,0,0.25)", color: mcColors.text }}
          />
          <button type="button" disabled={busy || !note.trim()} onClick={() => void saveNote()} style={{ ...mcButtonSecondaryStyle, marginTop: 8 }}>
            Save validation note
          </button>
        </div>
      </div>
    </section>
  );
}
