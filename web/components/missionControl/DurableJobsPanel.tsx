"use client";

import { useCallback, useEffect, useState } from "react";

import { approveMutationExecution } from "@/lib/missionControl/mutationArtifacts";
import { governedMutationSafetyCopy, pendingApprovalReviewLines, type PendingApprovalRecord } from "@/lib/missionControl/jobApprovalUx";
import { resolveVisibleNavigationPath } from "@/lib/missionControl/visibleNavigationRegistry";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import { mcFetch } from "@/lib/missionControl/fetch";
import { cancelTrackedJob } from "@/lib/missionControl/trackedJobs";

type Props = { view: MissionControlView };

type JobTruthState = {
  phase?: string;
  runtime_presence?: { summary?: string; presence?: string };
  freshness?: { freshness_tier?: string; freshness_phrase?: string };
  notification_digest?: string;
  pending_notifications?: number;
};

type ExternalExecutionState = {
  phase?: string;
  runner_mode?: string;
  external_runner_presence?: { summary?: string };
  orphaned_jobs?: Array<Record<string, unknown>>;
  jobs?: Array<Record<string, unknown>>;
  divergent_count?: number;
  webhook_security?: Record<string, boolean>;
  reconciliation?: { stale_callbacks?: Array<Record<string, unknown>> };
};

type TelegramSoakState = {
  phase?: string;
  continuity_drift?: { continuity_drift?: string; freshness?: { freshness_tier?: string } };
  notification_pressure?: { notification_pressure?: string; pending_count?: number };
  contradictions?: { divergent_count?: number; reconciliation_phrase?: string | null };
  operational_fatigue?: { fatigue?: string; unique_reply_ratio?: number };
  ledger?: { average_realism?: number; entry_count?: number };
};

type DurableJobsState = {
  ok?: boolean;
  phase?: string;
  trigger_enabled?: boolean;
  active_jobs?: Array<Record<string, unknown>>;
  recent_jobs?: Array<Record<string, unknown>>;
  continuity?: Record<string, unknown>;
  job_truth?: JobTruthState;
  external_execution?: ExternalExecutionState;
  telegram_soak?: TelegramSoakState;
};

export function DurableJobsPanel({ view }: Props) {
  const [state, setState] = useState<DurableJobsState | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<PendingApprovalRecord[]>([]);
  const [approvalBusy, setApprovalBusy] = useState<string | null>(null);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const sessionId = "operator";
      if (view === "cog-durable-jobs-active") {
        const data = await mcFetch<{ jobs: Record<string, unknown>[] }>(
          `/api/v1/jobs/durable/active?session_id=${sessionId}`,
        );
        setState({ ok: true, active_jobs: data.jobs, phase: "11.7.9" });
      } else if (view === "cog-durable-jobs-artifacts") {
        const data = await mcFetch<{ artifacts: Record<string, unknown>[] }>(
          `/api/v1/jobs/durable/artifacts?session_id=${sessionId}`,
        );
        setState({ ok: true, recent_jobs: data.artifacts as Record<string, unknown>[], phase: "11.7.9" });
      } else {
        const [durable, truth, external, soak, pending] = await Promise.all([
          mcFetch<DurableJobsState>(`/api/v1/jobs/durable/state?session_id=${sessionId}`),
          mcFetch<JobTruthState>(`/api/v1/job-truth/state?session_id=${sessionId}`),
          mcFetch<ExternalExecutionState>(`/api/v1/external-execution/state?session_id=${sessionId}`),
          mcFetch<TelegramSoakState>(`/api/v1/telegram-soak/state?session_id=${sessionId}`),
          mcFetch<{ pending_approvals: PendingApprovalRecord[] }>(
            `/api/v1/jobs/pending-approvals?session_id=${sessionId}`,
          ),
        ]);
        setPendingApprovals(pending.pending_approvals ?? []);
        setState({ ...durable, job_truth: truth, external_execution: external, telegram_soak: soak });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load durable jobs");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const jobs = state?.active_jobs ?? state?.recent_jobs ?? [];
  const soak = state?.telegram_soak;
  const external = state?.external_execution;
  const staleCallbacks = external?.reconciliation?.stale_callbacks?.length ?? 0;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>Durable Agent Jobs</h3>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}
      {state ? (
        <>
          <p style={{ fontSize: 13, color: mcColors.textMuted }}>
            Phase {external?.phase ?? state.job_truth?.phase ?? state.phase ?? "11.8.2"} ·{" "}
            Runner {external?.runner_mode ?? (state.trigger_enabled ? "external" : "embedded")}
          </p>
          {external?.external_runner_presence?.summary ? (
            <p style={{ fontSize: 13, color: mcColors.text, marginTop: 8 }}>
              {external.external_runner_presence.summary}
            </p>
          ) : null}
          {state.job_truth?.freshness?.freshness_phrase ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              External runtime freshness: {state.job_truth.freshness.freshness_tier} —{" "}
              {state.job_truth.freshness.freshness_phrase}
            </p>
          ) : null}
          {staleCallbacks > 0 ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              Active verification windows: {staleCallbacks} callback(s) outside fresh truth window
            </p>
          ) : null}
          {state.job_truth?.notification_digest ? (
            <p style={{ fontSize: 12, color: mcColors.textDim, marginTop: 8 }}>
              Notification digest: {state.job_truth.notification_digest}
            </p>
          ) : null}
          {soak?.notification_pressure?.notification_pressure ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              Retry pressure: {soak.notification_pressure.notification_pressure}
              {typeof soak.notification_pressure.pending_count === "number"
                ? ` (${soak.notification_pressure.pending_count} pending)`
                : ""}
            </p>
          ) : null}
          {typeof external?.divergent_count === "number" && external.divergent_count > 0 ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              Truth divergence: {external.divergent_count} job(s) with embedded/external mismatch
            </p>
          ) : soak?.contradictions?.reconciliation_phrase ? (
            <p style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 6 }}>
              {soak.contradictions.reconciliation_phrase}
            </p>
          ) : null}
          {soak?.ledger?.entry_count ? (
            <p style={{ fontSize: 12, color: mcColors.textDim, marginTop: 6 }}>
              Latest meaningful change: soak ledger avg realism {soak.ledger.average_realism ?? "—"} (
              {soak.ledger.entry_count} turns)
            </p>
          ) : null}
          {pendingApprovals.length > 0 ? (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>Governed mutations awaiting approval</h4>
              {pendingApprovals.map((pending) => (
                <div
                  key={pending.job_id}
                  style={{
                    padding: "12px",
                    marginBottom: 10,
                    borderRadius: 8,
                    border: `1px solid ${mcColors.borderSubtle}`,
                    fontSize: 13,
                  }}
                >
                  <strong>{pending.job_id}</strong>
                  <p style={{ margin: "8px 0", color: mcColors.textMuted, fontSize: 12 }}>
                    {pending.approval_surface ??
                      resolveVisibleNavigationPath("Operation Preflights", "operator")}
                  </p>
                  <ul style={{ margin: "8px 0", paddingLeft: 18, color: mcColors.textDim, fontSize: 12 }}>
                    {pendingApprovalReviewLines(pending).map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                  <p style={{ margin: "8px 0", fontSize: 12, color: mcColors.textMuted }}>
                    {governedMutationSafetyCopy(pending)}
                  </p>
                  <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                    <button
                      type="button"
                      style={mcButtonSecondaryStyle}
                      disabled={approvalBusy === pending.job_id || pending.ui_action_available === false}
                      onClick={() => {
                        setApprovalError(null);
                        setApprovalBusy(pending.job_id);
                        void approveMutationExecution(pending.job_id)
                          .then(() => load())
                          .catch((e: unknown) => {
                            setApprovalError(e instanceof Error ? e.message : "Approval failed");
                          })
                          .finally(() => setApprovalBusy(null));
                      }}
                    >
                      {approvalBusy === pending.job_id
                        ? "Approving…"
                        : pending.approval_action_label ?? "Approve Governed Mutation"}
                    </button>
                    <button
                      type="button"
                      style={mcButtonSecondaryStyle}
                      disabled={approvalBusy === pending.job_id}
                      onClick={() => {
                        setApprovalError(null);
                        setApprovalBusy(pending.job_id);
                        void cancelTrackedJob(pending.job_id)
                          .then(() => load())
                          .catch((e: unknown) => {
                            setApprovalError(e instanceof Error ? e.message : "Cancel failed");
                          })
                          .finally(() => setApprovalBusy(null));
                      }}
                    >
                      Reject / Cancel
                    </button>
                  </div>
                </div>
              ))}
              {approvalError ? (
                <p style={{ color: mcColors.red, fontSize: 12, marginTop: 6 }}>{approvalError}</p>
              ) : null}
            </div>
          ) : null}
          {jobs.length === 0 ? (
            <p style={{ fontSize: 13, color: mcColors.textDim }}>No jobs in this view.</p>
          ) : (
            jobs.map((job) => (
              <div
                key={String(job.job_id ?? job.summary ?? Math.random())}
                style={{
                  padding: "10px 12px",
                  marginBottom: 8,
                  borderRadius: 8,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  fontSize: 13,
                }}
              >
                <strong>{String(job.job_type ?? job.artifact_type ?? "job")}</strong>
                {" · "}
                {String(job.status ?? "artifact")}
                {job.entity_name ? ` · ${String(job.entity_name)}` : ""}
                {typeof job.retries === "number" && job.retries > 0 ? ` · retries ${String(job.retries)}` : ""}
              </div>
            ))
          )}
        </>
      ) : (
        <p style={{ fontSize: 13, color: mcColors.textDim }}>Loading…</p>
      )}
    </div>
  );
}
