"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  appendMissionControlDogfoodPilotTrustReportFreezeRecord,
  fetchMissionControlDogfoodPilotTrustReportFreeze,
} from "@/lib/missionControl/missionControlDogfoodPilotTrustReportFreezeApi";
import { fetchMissionControlDogfoodPilotGateClosure } from "@/lib/missionControl/missionControlDogfoodPilotGateClosureApi";
import {
  fetchMissionControlEndToEndRepoDevelopmentPilotHarness,
  runMissionControlEndToEndRepoDevelopmentPilotHarness,
} from "@/lib/missionControl/missionControlEndToEndRepoDevelopmentPilotHarnessApi";
import {
  appendMissionControlIssueIntentAlignmentRecord,
  fetchMissionControlIssueIntentAlignment,
} from "@/lib/missionControl/missionControlIssueIntentAlignmentApi";
import { fetchMissionControlIssueIntakeScopeFidelity } from "@/lib/missionControl/missionControlIssueIntakeScopeFidelityApi";
import {
  fetchMissionControlPilotValidationTrustBoard,
} from "@/lib/missionControl/missionControlPilotValidationTrustBoardApi";
import { fetchMissionControlRepoPilotReadinessDashboard } from "@/lib/missionControl/missionControlRepoPilotReadinessDashboardApi";

type Props = { sessionId?: string };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const sectionTitle = { fontWeight: 600, marginBottom: 8, color: mcColors.cyan } as const;

function errMsg(e: unknown, fallback: string) {
  return e instanceof Error ? e.message : fallback;
}

export function DogfoodPilotChainPanel({ sessionId = "operator" }: Props) {
  const [repoIssue, setRepoIssue] = useState("pilotmain/AethOS#1");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fix182, setFix182] = useState<Record<string, unknown> | null>(null);
  const [fix181, setFix181] = useState<Record<string, unknown> | null>(null);
  const [fix185, setFix185] = useState<Record<string, unknown> | null>(null);
  const [fix184, setFix184] = useState<Record<string, unknown> | null>(null);
  const [fix183, setFix183] = useState<Record<string, unknown> | null>(null);
  const [fix186, setFix186] = useState<Record<string, unknown> | null>(null);
  const [gateClosure, setGateClosure] = useState<Record<string, unknown> | null>(null);
  const [runDetail, setRunDetail] = useState<string | null>(null);
  const [freezeNote, setFreezeNote] = useState("");

  const load = useCallback(async () => {
    setError(null);
    const results = await Promise.allSettled([
      fetchMissionControlRepoPilotReadinessDashboard(sessionId, "json"),
      fetchMissionControlEndToEndRepoDevelopmentPilotHarness(sessionId, "json"),
      fetchMissionControlIssueIntakeScopeFidelity(sessionId),
      fetchMissionControlIssueIntentAlignment(sessionId, "json"),
      fetchMissionControlPilotValidationTrustBoard(sessionId, "json"),
      fetchMissionControlDogfoodPilotTrustReportFreeze(sessionId, "json"),
      fetchMissionControlDogfoodPilotGateClosure(sessionId),
    ]);
    const [r182, r181, r185, r184, r183, r186, rGate] = results;
    if (r182.status === "fulfilled") setFix182(r182.value.repo_pilot_readiness_dashboard as Record<string, unknown>);
    if (r181.status === "fulfilled")
      setFix181(r181.value.end_to_end_repo_development_pilot_harness as Record<string, unknown>);
    if (r185.status === "fulfilled") setFix185(r185.value as Record<string, unknown>);
    else setFix185(null);
    if (r184.status === "fulfilled") setFix184(r184.value.issue_intent_alignment as Record<string, unknown>);
    else setFix184(null);
    if (r183.status === "fulfilled")
      setFix183(r183.value.pilot_validation_trust_board as Record<string, unknown>);
    else setFix183(null);
    if (r186.status === "fulfilled")
      setFix186(r186.value.dogfood_pilot_trust_report_freeze as Record<string, unknown>);
    else setFix186(null);
    if (rGate.status === "fulfilled")
      setGateClosure(rGate.value.dogfood_pilot_gate_closure as Record<string, unknown>);
    else setGateClosure(null);
  }, [sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  const onRunPilot = async () => {
    setBusy(true);
    setRunDetail(null);
    try {
      const res = await runMissionControlEndToEndRepoDevelopmentPilotHarness(sessionId, repoIssue.trim());
      setRunDetail(
        res.ok
          ? `Pilot run ok — audit ${res.audit_id || "n/a"} · stages ${(res.stages_completed || []).join(", ") || "none"}`
          : `Pilot blocked: ${(res.blockers || []).join(", ") || res.detail || "unknown"}`,
      );
      await load();
    } catch (e) {
      setRunDetail(errMsg(e, "Pilot run failed"));
    } finally {
      setBusy(false);
    }
  };

  const onRecordFreeze = async () => {
    const text = freezeNote.trim();
    if (!text) return;
    setBusy(true);
    try {
      await appendMissionControlDogfoodPilotTrustReportFreezeRecord(sessionId, "trust_report_freeze_artifact", text);
      setFreezeNote("");
      await load();
    } catch (e) {
      setError(errMsg(e, "Failed to record trust freeze"));
    } finally {
      setBusy(false);
    }
  };

  const onAckAlignment = async () => {
    setBusy(true);
    try {
      await appendMissionControlIssueIntentAlignmentRecord(
        sessionId,
        "alignment_review",
        "Operator reviewed alignment gate during dogfood manual test.",
      );
      await load();
    } catch (e) {
      setError(errMsg(e, "Failed to record alignment review"));
    } finally {
      setBusy(false);
    }
  };

  const onRecordReview = async () => {
    setBusy(true);
    try {
      await appendMissionControlDogfoodPilotTrustReportFreezeRecord(
        sessionId,
        "operator_review_note",
        "Operator reviewed dogfood trust report freeze during FIX 181–186 manual gate.",
      );
      await load();
    } catch (e) {
      setError(errMsg(e, "Failed to record operator review"));
    } finally {
      setBusy(false);
    }
  };

  const checklist = (gateClosure?.checklist as Array<Record<string, unknown>>) || [];

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Dogfood Pilot Chain</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            FIX 182 → 181 → 185 → 184 → 183 → 186 — operational evidence path (session: {sessionId})
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12 }}>{error}</p> : null}
      {runDetail ? <p style={{ color: mcColors.cyan, marginTop: 12, fontSize: 13 }}>{runDetail}</p> : null}

      {gateClosure ? (
        <div style={{ ...cardStyle, marginTop: 16, borderColor: gateClosure.gate_complete ? mcColors.cyan : mcColors.amber }}>
          <div style={sectionTitle}>
            FIX 181–186 gate closure — {gateClosure.gate_complete ? "complete" : "partial"} (
            {String(gateClosure.gates_passed ?? 0)}/{String(gateClosure.gates_total ?? 6)})
          </div>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: mcColors.textDim }}>
            {checklist.map((row) => (
              <li key={String(row.fix)}>
                {row.passed ? "✓" : "○"} {String(row.fix)} — {String(row.gate)}
              </li>
            ))}
          </ul>
          {gateClosure.gate_complete ? (
            <div style={{ fontSize: 12, color: mcColors.cyan, marginTop: 8 }}>
              Next: {String(gateClosure.next_phase ?? "FIX 187")}
            </div>
          ) : null}
        </div>
      ) : null}

      <div style={{ marginTop: 16 }}>
        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 182 — Repo pilot readiness</div>
          <div style={{ color: mcColors.textDim }}>
            Repos assessed: {String((fix182?.sources as Record<string, unknown>)?.accessible_repos ?? "—")}
          </div>
          <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>
            Chat: show pilot readiness · readiness repo: pilotmain/AethOS
          </div>
        </div>

        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 181 — End-to-end pilot harness</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
            <input
              value={repoIssue}
              onChange={(e) => setRepoIssue(e.target.value)}
              placeholder="pilotmain/AethOS#1"
              style={{
                flex: 1,
                minWidth: 200,
                padding: "6px 8px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.25)",
                color: mcColors.text,
              }}
            />
            <button type="button" disabled={busy} onClick={() => void onRunPilot()} style={mcButtonSecondaryStyle}>
              Run pilot (chat governance)
            </button>
          </div>
          <div style={{ fontSize: 12, color: mcColors.textDim }}>
            Pilot audits: {String(fix181?.pilot_run_audits ?? fix181?.sources ?? "—")} · Terminal: pr_open
          </div>
        </div>

        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 185 — Issue intake scope fidelity</div>
          {fix185 ? (
            <>
              <div>Fidelity score: {String((fix185.assessment as Record<string, unknown>)?.fidelity_score ?? "—")}</div>
              <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>
                Expected files:{" "}
                {JSON.stringify(
                  (fix185.issue_intake_scope_fidelity as Record<string, unknown>)?.expected_files ?? [],
                )}
              </div>
            </>
          ) : (
            <div style={{ color: mcColors.textMuted }}>No issue plan yet — analyze GitHub issue first.</div>
          )}
        </div>

        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 184 — Intent alignment</div>
          {fix184 ? (
            <>
              <div>Alignment score: {String(fix184.alignment_score ?? "—")}</div>
              <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>
                Gate: {String(fix184.intent_alignment_gate_status ?? fix184.alignment_gate_status ?? "—")}
              </div>
              <button type="button" disabled={busy} onClick={() => void onAckAlignment()} style={{ ...mcButtonSecondaryStyle, marginTop: 8 }}>
                Record alignment review
              </button>
            </>
          ) : (
            <div style={{ color: mcColors.textMuted }}>Alignment board unavailable until plan + patch stage.</div>
          )}
        </div>

        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 183 — Pilot validation trust</div>
          {fix183 ? (
            <>
              <div>Trust: {String(fix183.trust_recommendation ?? "—")}</div>
              <div>Human effort score: {String(fix183.human_effort_score ?? "—")}</div>
            </>
          ) : (
            <div style={{ color: mcColors.textMuted }}>Requires FIX 181 pilot run audits.</div>
          )}
        </div>

        <div style={cardStyle}>
          <div style={sectionTitle}>FIX 186 — Dogfood trust report freeze</div>
          {fix186 ? (
            <>
              <div>Trust status: {String(fix186.trust_status ?? fix186.trust_recommendation ?? "—")}</div>
              <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>
                Multi-repo expansion blocked: {String(fix186.multi_repo_expansion_blocked ?? "—")}
              </div>
            </>
          ) : (
            <div style={{ color: mcColors.textMuted }}>Requires completed pilot audits (181) and validation (183).</div>
          )}
          <textarea
            value={freezeNote}
            onChange={(e) => setFreezeNote(e.target.value)}
            placeholder="trust report freeze: Pilots 1–3 baseline recorded"
            rows={2}
            style={{
              width: "100%",
              marginTop: 8,
              fontSize: 12,
              padding: 8,
              borderRadius: 8,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.25)",
              color: mcColors.text,
            }}
          />
          <button type="button" disabled={busy || !freezeNote.trim()} onClick={() => void onRecordFreeze()} style={{ ...mcButtonSecondaryStyle, marginTop: 8 }}>
            Record trust freeze note
          </button>
          <button type="button" disabled={busy} onClick={() => void onRecordReview()} style={{ ...mcButtonSecondaryStyle, marginTop: 8, marginLeft: 8 }}>
            Record operator review
          </button>
        </div>
      </div>
    </section>
  );
}
