"use client";

import { useCallback, useState, type CSSProperties } from "react";

import {
  copyArtifactText,
  downloadArtifactMarkdown,
  jobArtifactPreview,
  jobArtifactSummary,
  jobFullReport,
} from "@/lib/missionControl/jobArtifacts";
import {
  vercelAuthMethodLabel,
  vercelAuthRef,
  type VercelJobParams,
} from "@/lib/missionControl/vercelAuthMethod";
import { artifactReportPreStyle } from "@/lib/missionControl/layout";
import {
  cancelTrackedJob,
  externalJobMode,
  externalJobTarget,
  jobControlHint,
  normalizeJobsGrouped,
  usesExternalJobType,
  type JobsGrouped,
  type TrackedJobRecord,
} from "@/lib/missionControl/trackedJobs";
import { formatMcPanelError } from "@/lib/missionControl/panelError";
import { trackJobId } from "@/lib/chat/jobLifecycleBridge";
import {
  approveMutationExecution,
  blastRadiusFromJob,
  canApproveMutationExecution,
  credentialGuidanceFromJob,
  fetchRailwayTargets,
  isCredentialBlockedPreflight,
  isMutationExecutionJob,
  isMutationPreflightJob,
  isCurrentMutationPreflight,
  mutationEvidenceTitle,
  mutationExecutionJobId,
  mutationExecutionLabel,
  mutationExecutionStatusLabel,
  railwayRestartEvidenceFromJob,
  railwayRestartEvidenceLabel,
  providerEvidenceCardsFromJob,
  providerEvidenceCardsLabel,
  mutationLifecycleDisplay,
  mutationPreflightFromJob,
  mutationPreflightStatus,
  mutationRiskLabel,
  mutationStatusLabel,
  mutationTimelineSteps,
  operationLifecycleFromJob,
  operationLifecycleSummary,
  postMutationVerificationFromJob,
  postMutationVerificationSummary,
  repairLearningFromJob,
  repairLearningSummary,
  partitionMutationJobs,
  refreshCredentialsAndPreflight,
  refreshJobTargets,
  resolveJobTarget,
  targetMetadataFromJob,
  targetResolvedFromJob,
} from "@/lib/missionControl/mutationArtifacts";
import { resolvedTargetPathFromJob } from "@/lib/missionControl/providerDiscovery";
import {
  mutationExecutionStateLabel,
  mutationFailureClassificationLabel,
  mutationLifecycleSummary,
  mutationVerificationStateLabel,
} from "@/lib/missionControl/mutationAudit";
import {
  approveReadonlyExecution,
  canApproveReadonlyExecution,
  executionConfidenceLabel,
  executionDataSourceLabel,
  executionEvidenceByTier,
  executionEvidenceFromJob,
  executionJobIdFromPreflight,
  executionOperationalEventsFromJob,
  executionTimelineFromJob,
  formatExecutionDebugEvidenceLabel,
  formatExecutionEvidenceLabel,
  formatOperationalEventAt,
  isCurrentPreflight,
  isOperationPreflightJob,
  isReadonlyExecutionJob,
  isReadonlyExecutionTimedOut,
  mcJobAnchorId,
  missingInfoQuestions,
  operationPreflightFromJob,
  orchestrationLifecycleDisplay,
  orchestrationOperationFromJob,
  orchestrationProviderFromJob,
  partitionCompletedJobs,
  partitionGroupedJobs,
  partitionPreflights,
  preflightDebugState,
  preflightExecutionLabel,
  preflightExecutionStatusLines,
  preflightStatusLabel,
  productionImpactLabel,
  readonlyExecutionBadge,
  readonlyExecutionCardMeta,
  readonlyExecutionsEmpty,
} from "@/lib/missionControl/operationPreflight";
import {
  formatProviderEvidenceItem,
  providerEvidenceSectionTitle,
} from "@/lib/missionControl/providerEvidence";
import {
  isVercelReadonlyJob,
  splitFullReportSections,
  vercelInventoryFromJob,
} from "@/lib/missionControl/vercelArtifact";

type Props = {
  jobs: JobsGrouped;
  onRefresh: () => void;
  mode?: "all" | "tracked" | "preflights";
};

function CompletedJobRow({ job, onRefresh }: { job: TrackedJobRecord; onRefresh: () => void }) {
  const [open, setOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [approving, setApproving] = useState(false);
  const [mutationApproving, setMutationApproving] = useState(false);
  const [approveError, setApproveError] = useState("");
  const [mutationApproveError, setMutationApproveError] = useState("");
  const [resolveTargetOpen, setResolveTargetOpen] = useState(false);
  const [targetCandidates, setTargetCandidates] = useState<Array<Record<string, unknown>>>([]);
  const [manualTargetName, setManualTargetName] = useState("");
  const [targetResolving, setTargetResolving] = useState(false);
  const [targetResolveError, setTargetResolveError] = useState("");
  const [credentialRefreshing, setCredentialRefreshing] = useState(false);
  const [credentialRefreshError, setCredentialRefreshError] = useState("");
  const preview = jobArtifactPreview(job);
  const summary = jobArtifactSummary(job);
  const full = jobFullReport(job);
  const vercelInv = isVercelReadonlyJob(job) ? vercelInventoryFromJob(job) : null;
  const opPreflight = isOperationPreflightJob(job) ? operationPreflightFromJob(job) : null;
  const mutationPreflight = isMutationPreflightJob(job) ? mutationPreflightFromJob(job) : null;
  const mutationBlast = isMutationPreflightJob(job) ? blastRadiusFromJob(job) : null;
  const mutationTargetMeta = isMutationPreflightJob(job) ? targetMetadataFromJob(job) : null;
  const mutationTargetResolved = isMutationPreflightJob(job) ? targetResolvedFromJob(job) : false;
  const mutationCredentialGuidance = isMutationPreflightJob(job) ? credentialGuidanceFromJob(job) : null;
  const mutationCredentialBlocked = isMutationPreflightJob(job) ? isCredentialBlockedPreflight(job) : false;
  const mutationLifecycle = isMutationPreflightJob(job) ? operationLifecycleFromJob(job) : null;
  const postMutationVerification = postMutationVerificationFromJob(job);
  const repairLearning = repairLearningFromJob(job);
  const execTimeline = isReadonlyExecutionJob(job) ? executionTimelineFromJob(job) : [];
  const { main: reportMain, debug: reportDebug, extractionDebug } = splitFullReportSections(full);
  const memoryFallback = Boolean(vercelInv?.memory_fallback);

  const handleCopy = async () => {
    const ok = await copyArtifactText(job);
    setCopied(ok);
    if (ok) window.setTimeout(() => setCopied(false), 2000);
  };

  const execMeta = isReadonlyExecutionJob(job) ? readonlyExecutionCardMeta(job) : null;
  const orchestrationProvider = orchestrationProviderFromJob(job);
  const orchestrationOperation = orchestrationOperationFromJob(job);

  return (
    <li
      id={mcJobAnchorId(job.id)}
      style={{
        padding: 12,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600 }}>{job.title}</div>
      {execMeta && (
        <div
          style={{
            marginTop: 8,
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(134,239,172,0.25)",
            background: "rgba(134,239,172,0.06)",
            fontSize: 12,
            color: "var(--aethos-text)",
            lineHeight: 1.55,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Read-only execution result</div>
          <div>
            Operation: <strong>{execMeta.operation}</strong> · Target: <strong>{execMeta.target}</strong>
          </div>
          <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
            {execMeta.provider} · Auth: {execMeta.authMethod} · {execMeta.dataSource}
          </div>
          <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
            Status: {jobControlHint(job.status)}
            {formatExecutionEvidenceLabel(job)
              ? ` · ${formatExecutionEvidenceLabel(job)}`
              : execMeta.evidenceCount > 0
                ? ` · Evidence: ${execMeta.evidenceCount}`
                : ""}
            {execMeta.timelineCount > 0 ? ` · Timeline: ${execMeta.timelineCount}` : ""}
          </div>
          {isReadonlyExecutionTimedOut(job) && (
            <div style={{ marginTop: 6, color: "var(--aethos-warn)" }}>Timed out — no indefinite running state.</div>
          )}
        </div>
      )}
      <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
        {jobControlHint(job.status)} · {orchestrationLifecycleDisplay(job)} · <code>{job.id}</code>
      </div>
      {usesExternalJobType(job.job_type) && (
        <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>
          External health · Target: {externalJobTarget(job)} · Mode: {externalJobMode(job)}
          {typeof job.params?.tool_used === "string" ? ` · Tool: ${job.params.tool_used}` : ""}
        </div>
      )}
      {job.provider_used && !usesExternalJobType(job.job_type) && (
        <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>
          Provider: {job.provider_used}
          {job.model_used ? ` · Model: ${job.model_used}` : ""}
          {job.params?.provider_fallback === true ? " · Fallback template" : ""}
        </div>
      )}
      {usesExternalJobType(job.job_type) && job.provider_used && (
        <div style={{ color: "var(--aethos-text-muted)", marginTop: 2, fontSize: 12 }}>
          Provider: {job.provider_used}
          {job.model_used ? ` · ${job.model_used}` : ""}
        </div>
      )}
      {isVercelReadonlyJob(job) && (
        <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>
          Auth: {vercelAuthMethodLabel(job.params as VercelJobParams)}
          {(() => {
            const ref = vercelAuthRef(job.params as VercelJobParams);
            return ref ? (
              <>
                {" "}
                · <code>{ref}</code>
              </>
            ) : null;
          })()}
          {typeof job.params?.browser_used === "boolean"
            ? ` · Browser: ${job.params.browser_used ? "yes" : "no"}`
            : ""}
          {typeof job.params?.provider_used === "string"
            ? ` · Provider: ${job.params.provider_used}`
            : ""}
          {typeof job.params?.project_count === "number" ? ` · ${job.params.project_count} projects` : ""}
        </div>
      )}
      {opPreflight && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(251,191,36,0.25)",
            background: "rgba(251,191,36,0.06)",
            fontSize: 12,
            color: "var(--aethos-text)",
            lineHeight: 1.55,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Operation preflight</div>
          <div style={{ color: "var(--aethos-text-muted)", marginBottom: 4 }}>
            {preflightStatusLabel(job)}
            {!isCurrentPreflight(job) ? " · previous attempt" : ""}
          </div>
          <div>
            Target: <strong>{resolvedTargetPathFromJob(job) ?? opPreflight.target_name ?? "(unresolved)"}</strong>
            {opPreflight.target_status ? ` · ${opPreflight.target_status}` : ""}
          </div>
          <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
            {opPreflight.provider ?? "unknown"} · {opPreflight.operation_type ?? job.job_type}
            {opPreflight.risk_level ? ` · Risk: ${opPreflight.risk_level}` : ""}
          </div>
          {preflightExecutionStatusLines(job).length > 0 && (
            <div style={{ marginTop: 6, color: "var(--aethos-text)" }}>
              {preflightExecutionStatusLines(job).map((line) => (
                <div key={line}>{line}</div>
              ))}
            </div>
          )}
          {(opPreflight.proposed_steps?.length ?? 0) > 0 && (
            <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
              {(opPreflight.proposed_steps ?? []).slice(0, 5).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          )}
          {(opPreflight.blockers?.length ?? 0) > 0 && (
            <div style={{ marginTop: 6, color: "var(--aethos-warn)" }}>
              {(opPreflight.blockers ?? []).map((b) => (
                <div key={b}>{b}</div>
              ))}
            </div>
          )}
          {(() => {
            const debugState = preflightDebugState(job);
            const keys = Object.keys(debugState);
            if (keys.length === 0) return null;
            return (
              <details style={{ marginTop: 6 }}>
                <summary style={{ cursor: "pointer", color: "var(--aethos-text-muted)" }}>Debug target resolution</summary>
                <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                  {keys.map((key) => (
                    <li key={key}>
                      <code>{key}</code>: {String(debugState[key])}
                    </li>
                  ))}
                </ul>
              </details>
            );
          })()}
          {missingInfoQuestions(job).length > 0 && (
            <div style={{ marginTop: 6, color: "var(--aethos-text)" }}>
              <div style={{ fontWeight: 600 }}>Still needed</div>
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {missingInfoQuestions(job).map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </div>
          )}
          {executionJobIdFromPreflight(job) && (
            <a
              href={`#${mcJobAnchorId(executionJobIdFromPreflight(job)!)}`}
              style={{
                display: "inline-block",
                marginTop: 8,
                color: "var(--aethos-ok)",
                fontSize: 12,
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              View execution result: {executionJobIdFromPreflight(job)}
            </a>
          )}
          <button
            type="button"
            disabled={!canApproveReadonlyExecution(job) || approving}
            title={
              canApproveReadonlyExecution(job)
                ? "Approve read-only execution for this preflight"
                : "Complete preflight and resolve missing info before approval"
            }
            onClick={() => {
              setApproveError("");
              setApproving(true);
              void approveReadonlyExecution(job.id)
                .then((res) => {
                  const execId = res.execution_job?.id;
                  if (typeof execId === "string" && execId) trackJobId(execId);
                  onRefresh();
                })
                .catch((e: unknown) => {
                  setApproveError(e instanceof Error ? e.message : "Approval failed");
                })
                .finally(() => setApproving(false));
            }}
            style={{
              ...artifactButtonStyle(canApproveReadonlyExecution(job) ? "var(--aethos-ok)" : "var(--aethos-text-dim)"),
              marginTop: 8,
              opacity: canApproveReadonlyExecution(job) ? 1 : 0.65,
              cursor: canApproveReadonlyExecution(job) ? "pointer" : "not-allowed",
            }}
          >
            {approving ? "Approving…" : preflightExecutionLabel(job)}
          </button>
          {approveError && (
            <div style={{ marginTop: 6, color: "var(--aethos-warn)", fontSize: 12 }}>{approveError}</div>
          )}
        </div>
      )}
      {mutationPreflight && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(248,113,113,0.25)",
            background: "rgba(248,113,113,0.06)",
            fontSize: 12,
            color: "var(--aethos-text)",
            lineHeight: 1.55,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Mutation preflight</div>
          <div style={{ color: "var(--aethos-text-muted)", marginBottom: 4 }}>
            {mutationStatusLabel(job)} · {mutationPreflightStatus(job).replace(/_/g, " ")}
            {mutationRiskLabel(job) ? ` · ${mutationRiskLabel(job)}` : ""}
          </div>
          <div style={{ color: "var(--aethos-text-dim)", fontSize: 11, marginBottom: 6 }}>
            {mutationTimelineSteps(job).join(" → ")}
          </div>
          <div>
            Target:{" "}
            <strong>
              {resolvedTargetPathFromJob(job) ??
                mutationPreflight.target_name ??
                (mutationTargetResolved ? "resolved" : "(unresolved)")}
            </strong>
          </div>
          {mutationTargetMeta?.project_name ? (
            <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
              Project: <strong>{String(mutationTargetMeta.project_name)}</strong>
              {mutationTargetMeta.environment ? (
                <>
                  {" "}
                  · Environment: <strong>{String(mutationTargetMeta.environment)}</strong>
                </>
              ) : null}
            </div>
          ) : null}
          {!mutationTargetResolved ? (
            <div style={{ marginTop: 6, color: "var(--aethos-warn)", fontSize: 11 }}>
              Approval blocked · Resolve target before approval
            </div>
          ) : mutationPreflightStatus(job) === "ready_for_mutation_approval" ? (
            <div style={{ marginTop: 6, color: "var(--aethos-ok)", fontSize: 11 }}>Approval: ready</div>
          ) : null}
          <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
            {mutationPreflight.provider ?? "unknown"} · {mutationPreflight.operation_type ?? job.job_type}
          </div>
          {mutationLifecycle && (mutationLifecycle.execution_status === "completed" || mutationLifecycle.execution_job_id) && (
            <div
              style={{
                marginTop: 10,
                padding: 10,
                borderRadius: 8,
                border: "1px solid rgba(134,239,172,0.25)",
                background: "rgba(134,239,172,0.06)",
                color: "var(--aethos-ok)",
                fontSize: 11,
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Latest lifecycle state</div>
              <div>
                Preflight:{" "}
                <strong>{String(mutationLifecycle.approval_status ?? "unknown").replace(/_/g, " ")}</strong>
              </div>
              {mutationLifecycle.execution_status && mutationLifecycle.execution_status !== "none" ? (
                <div>
                  Execution: <strong>{mutationLifecycle.execution_status}</strong>
                </div>
              ) : null}
              {mutationLifecycle.verification_status && mutationLifecycle.verification_status !== "none" ? (
                <div>
                  Verification: <strong>{mutationLifecycle.verification_status}</strong>
                </div>
              ) : null}
              {operationLifecycleSummary(job) ? (
                <div style={{ marginTop: 6, color: "var(--aethos-ok)" }}>{operationLifecycleSummary(job)}</div>
              ) : null}
              {mutationLifecycle.execution_job_id ? (
                <a
                  href={`#${mcJobAnchorId(mutationLifecycle.execution_job_id)}`}
                  style={{ display: "inline-block", marginTop: 8, color: "var(--aethos-ok)", fontWeight: 600 }}
                >
                  View execution: {mutationLifecycle.execution_job_id}
                </a>
              ) : null}
              {postMutationVerification ? (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: "1px solid rgba(134,239,172,0.2)" }}>
                  <div style={{ fontWeight: 700, marginBottom: 4 }}>Verification</div>
                  <div>
                    Status: <strong>{String(postMutationVerification.status ?? "unknown").replace(/_/g, " ")}</strong>
                  </div>
                  {postMutationVerification.service_health ? (
                    <div>Health: {postMutationVerification.service_health}</div>
                  ) : null}
                  {postMutationVerification.evidence_summary ? (
                    <div style={{ marginTop: 4, color: "var(--aethos-ok)" }}>
                      Evidence: {postMutationVerification.evidence_summary}
                    </div>
                  ) : null}
                  <div style={{ marginTop: 6, color: "var(--aethos-ok)" }}>
                    Actions: verify health · fetch logs · compare before/after
                  </div>
                </div>
              ) : null}
            </div>
          )}
          {mutationBlast && (
            <div style={{ marginTop: 6, color: "var(--aethos-text)" }}>
              <div style={{ fontWeight: 600 }}>Blast radius</div>
              <div>Scope: {String(mutationBlast.scope ?? "unknown")}</div>
              <div>Reversibility: {String(mutationBlast.reversibility ?? "unknown")}</div>
              <div>Downtime: {String(mutationBlast.expected_downtime ?? "unknown")}</div>
            </div>
          )}
          {mutationPreflight.rollback_plan && (
            <div style={{ marginTop: 6, color: "var(--aethos-text)" }}>
              Rollback: {String((mutationPreflight.rollback_plan as Record<string, unknown>).strategy ?? "—")}
            </div>
          )}
          {mutationCredentialBlocked && (
            <div
              style={{
                marginTop: 10,
                padding: 10,
                borderRadius: 8,
                border: "1px solid rgba(251,191,36,0.35)",
                background: "rgba(251,191,36,0.08)",
                color: "var(--aethos-warn)",
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Missing credential</div>
              <div style={{ fontFamily: "monospace", fontSize: 12, marginBottom: 8 }}>
                {mutationCredentialGuidance?.missing_credentials?.[0] ?? "Provider API token"}
              </div>
              {mutationCredentialGuidance?.why_needed ? (
                <div style={{ color: "var(--aethos-text)", fontSize: 11, marginBottom: 8 }}>
                  {mutationCredentialGuidance.why_needed}
                </div>
              ) : null}
              <div style={{ fontWeight: 600, marginBottom: 4, color: "var(--aethos-warn)" }}>Setup options</div>
              <ul style={{ margin: "0 0 8px 16px", padding: 0, color: "var(--aethos-text)", fontSize: 11 }}>
                {(mutationCredentialGuidance?.setup_steps ?? []).map((step) => (
                  <li key={`${step.kind}-${step.label}`}>{step.label}</li>
                ))}
              </ul>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  disabled={credentialRefreshing}
                  onClick={() => {
                    setCredentialRefreshError("");
                    setCredentialRefreshing(true);
                    void refreshCredentialsAndPreflight()
                      .then(() => onRefresh())
                      .catch((e: unknown) => {
                        setCredentialRefreshError(e instanceof Error ? e.message : "Credential refresh failed");
                      })
                      .finally(() => setCredentialRefreshing(false));
                  }}
                  style={artifactButtonStyle("var(--aethos-warn)")}
                >
                  {credentialRefreshing ? "Refreshing…" : "Refresh credentials"}
                </button>
                <button
                  type="button"
                  disabled={credentialRefreshing}
                  onClick={() => {
                    setCredentialRefreshError("");
                    setCredentialRefreshing(true);
                    void refreshCredentialsAndPreflight(job.id)
                      .then(() => onRefresh())
                      .catch((e: unknown) => {
                        setCredentialRefreshError(e instanceof Error ? e.message : "Preflight rerun failed");
                      })
                      .finally(() => setCredentialRefreshing(false));
                  }}
                  style={artifactButtonStyle("var(--aethos-warn)")}
                >
                  {credentialRefreshing ? "Re-running…" : "Re-run preflight"}
                </button>
              </div>
              {credentialRefreshError ? (
                <div style={{ marginTop: 6, color: "var(--aethos-danger)", fontSize: 11 }}>{credentialRefreshError}</div>
              ) : null}
            </div>
          )}
          {(() => {
            const debug =
              (job.params?.workflow_resolution_debug as Record<string, unknown> | undefined) ??
              ((mutationPreflight as Record<string, unknown>).workflow_resolution_debug as
                | Record<string, unknown>
                | undefined);
            if (!debug || mutationPreflightStatus(job) !== "needs_workflow_resolution") return null;
            return (
              <div style={{ marginTop: 8, color: "var(--aethos-warn)", fontSize: 11 }}>
                <div style={{ fontWeight: 600 }}>Discovery diagnostics</div>
                <div>Candidates: {String(debug.workflow_candidates_found ?? 0)}</div>
                <div>Rerunnable: {String(debug.rerunnable_candidates_found ?? 0)}</div>
                <div>
                  States:{" "}
                  {Array.isArray(debug.candidate_states)
                    ? (debug.candidate_states as string[]).join(", ")
                    : "—"}
                </div>
                <div>Reason: {String(debug.discovery_failure_reason ?? job.params?.discovery_failure_reason ?? "—")}</div>
              </div>
            );
          })()}
          {mutationExecutionJobId(job) && (
            <a
              href={`#${mcJobAnchorId(mutationExecutionJobId(job)!)}`}
              style={{
                display: "inline-block",
                marginTop: 8,
                color: "var(--aethos-danger)",
                fontSize: 12,
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              View mutation execution: {mutationExecutionJobId(job)}
            </a>
          )}
          {!mutationTargetResolved && (
            <div style={{ marginTop: 8 }}>
              <button
                type="button"
                onClick={() => {
                  setTargetResolveError("");
                  setResolveTargetOpen((open) => !open);
                  if (!resolveTargetOpen && targetCandidates.length === 0) {
                    void refreshJobTargets(job.id)
                      .then((res) => setTargetCandidates(res.candidates ?? []))
                      .catch(() =>
                        fetchRailwayTargets()
                          .then((res) => setTargetCandidates(res.candidates ?? []))
                          .catch((e: unknown) => {
                            setTargetResolveError(e instanceof Error ? e.message : "Could not load targets");
                          }),
                      );
                  }
                }}
                style={{
                  ...artifactButtonStyle("var(--aethos-warn)"),
                  marginTop: 0,
                }}
              >
                {resolveTargetOpen ? "Hide target resolver" : "Resolve target"}
              </button>
              {resolveTargetOpen && (
                <div style={{ marginTop: 8, color: "var(--aethos-text)" }}>
                  {targetCandidates.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>Candidate services</div>
                      {targetCandidates.slice(0, 6).map((row) => {
                        const name = String(row.service_name ?? row.name ?? "");
                        if (!name) return null;
                        return (
                          <button
                            key={name}
                            type="button"
                            disabled={targetResolving}
                            onClick={() => {
                              setTargetResolveError("");
                              setTargetResolving(true);
                              void resolveJobTarget(job.id, name)
                                .then(() => {
                                  setResolveTargetOpen(false);
                                  onRefresh();
                                })
                                .catch((e: unknown) => {
                                  setTargetResolveError(e instanceof Error ? e.message : "Resolve failed");
                                })
                                .finally(() => setTargetResolving(false));
                            }}
                            style={{
                              ...artifactButtonStyle("var(--aethos-accent)"),
                              display: "block",
                              width: "100%",
                              textAlign: "left",
                              marginTop: 4,
                            }}
                          >
                            {name}
                            {row.project_name ? ` (${String(row.project_name)})` : ""}
                          </button>
                        );
                      })}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <input
                      value={manualTargetName}
                      onChange={(e) => setManualTargetName(e.target.value)}
                      placeholder="Exact Railway service name"
                      style={{
                        flex: 1,
                        padding: "6px 8px",
                        borderRadius: 8,
                        border: "1px solid rgba(255,255,255,0.15)",
                        background: "rgba(0,0,0,0.2)",
                        color: "var(--aethos-text)",
                        fontSize: 12,
                      }}
                    />
                    <button
                      type="button"
                      disabled={targetResolving || !manualTargetName.trim()}
                      onClick={() => {
                        setTargetResolveError("");
                        setTargetResolving(true);
                        void resolveJobTarget(job.id, manualTargetName.trim())
                          .then(() => {
                            setResolveTargetOpen(false);
                            setManualTargetName("");
                            onRefresh();
                          })
                          .catch((e: unknown) => {
                            setTargetResolveError(e instanceof Error ? e.message : "Resolve failed");
                          })
                          .finally(() => setTargetResolving(false));
                      }}
                      style={artifactButtonStyle("var(--aethos-ok)")}
                    >
                      {targetResolving ? "Resolving…" : "Apply"}
                    </button>
                    <button
                      type="button"
                      disabled={targetResolving}
                      onClick={() => {
                        setTargetResolveError("");
                        void refreshJobTargets(job.id)
                          .then((res) => setTargetCandidates(res.candidates ?? []))
                          .catch((e: unknown) => {
                            setTargetResolveError(e instanceof Error ? e.message : "Refresh failed");
                          });
                      }}
                      style={artifactButtonStyle("var(--aethos-text-muted)")}
                    >
                      Refresh
                    </button>
                  </div>
                  {targetResolveError && (
                    <div style={{ marginTop: 6, color: "var(--aethos-warn)", fontSize: 12 }}>{targetResolveError}</div>
                  )}
                </div>
              )}
            </div>
          )}
          <button
            type="button"
            disabled={!canApproveMutationExecution(job) || mutationApproving}
            title={
              canApproveMutationExecution(job)
                ? "Approve governed mutation execution"
                : "Complete preflight and enable mutation execution before approval"
            }
            onClick={() => {
              setMutationApproveError("");
              setMutationApproving(true);
              void approveMutationExecution(job.id)
                .then((res) => {
                  const execId = res.mutation_execution_job?.id;
                  if (typeof execId === "string" && execId) trackJobId(execId);
                  onRefresh();
                })
                .catch((e: unknown) => {
                  setMutationApproveError(e instanceof Error ? e.message : "Mutation approval failed");
                })
                .finally(() => setMutationApproving(false));
            }}
            style={{
              ...artifactButtonStyle(canApproveMutationExecution(job) ? "var(--aethos-danger)" : "var(--aethos-text-dim)"),
              marginTop: 8,
              opacity: canApproveMutationExecution(job) ? 1 : 0.65,
              cursor: canApproveMutationExecution(job) ? "pointer" : "not-allowed",
            }}
          >
            {mutationApproving ? "Approving…" : mutationExecutionLabel(job)}
          </button>
          {mutationApproveError && (
            <div style={{ marginTop: 6, color: "var(--aethos-warn)", fontSize: 12 }}>{mutationApproveError}</div>
          )}
        </div>
      )}
      {isMutationExecutionJob(job) && (
        <div style={{ color: "var(--aethos-danger)", marginTop: 4, fontSize: 12 }}>
          Execution: {mutationExecutionStatusLabel(job)} · Verification:{" "}
          {mutationVerificationStateLabel(job)}
          {postMutationVerificationSummary(job) ? ` · ${postMutationVerificationSummary(job)}` : ""}
          {repairLearningSummary(job) ? ` · ${repairLearningSummary(job)}` : ""}
          {mutationFailureClassificationLabel(job)
            ? ` · Classification: ${mutationFailureClassificationLabel(job)}`
            : ""}
          {mutationEvidenceTitle(job) ? ` · ${mutationEvidenceTitle(job)}` : ""}
          {(() => {
            const restartEvidence = railwayRestartEvidenceFromJob(job);
            return restartEvidence ? ` · ${railwayRestartEvidenceLabel(restartEvidence)}` : "";
          })()}
          {(() => {
            const cards = providerEvidenceCardsFromJob(job);
            return cards ? ` · ${providerEvidenceCardsLabel(cards)}` : "";
          })()}
          {job.params?.verification_job_id ? (
            <>
              {" "}
              ·{" "}
              <a
                href={`#${mcJobAnchorId(String(job.params.verification_job_id))}`}
                style={{ color: "var(--aethos-danger)" }}
              >
                verification {String(job.params.verification_job_id)}
              </a>
            </>
          ) : null}
        </div>
      )}
      {isMutationExecutionJob(job) && postMutationVerification ? (
        <div
          style={{
            marginTop: 8,
            padding: 10,
            borderRadius: 8,
            border: "1px solid rgba(252,165,165,0.25)",
            background: "rgba(252,165,165,0.06)",
            color: "var(--aethos-danger)",
            fontSize: 11,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Post-mutation verification</div>
          <div>
            Status: <strong>{String(postMutationVerification.status ?? "unknown").replace(/_/g, " ")}</strong>
          </div>
          {postMutationVerification.last_checked_at ? (
            <div>Last checked: {String(postMutationVerification.last_checked_at)}</div>
          ) : null}
          <div>Health: {postMutationVerification.service_health ?? "unknown"}</div>
          <div>
            Provider command: {postMutationVerification.provider_command_submitted ? "submitted" : "unknown"}
          </div>
          <div>
            Logs after execution: {postMutationVerification.logs_after_execution ? "present" : "missing"}
          </div>
          {(postMutationVerification.before_status || postMutationVerification.after_status) && (
            <div style={{ marginTop: 4 }}>
              Before/after: {postMutationVerification.before_status || "—"} →{" "}
              {postMutationVerification.after_status || "—"}
            </div>
          )}
          <div style={{ marginTop: 6, color: "var(--aethos-danger)" }}>
            Actions: verify health · fetch logs · compare before/after
          </div>
        </div>
      ) : null}
      {isMutationExecutionJob(job) && repairLearning ? (
        <div
          style={{
            marginTop: 8,
            padding: 10,
            borderRadius: 8,
            border: "1px solid rgba(251,191,36,0.25)",
            background: "rgba(251,191,36,0.06)",
            color: "var(--aethos-warn)",
            fontSize: 11,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Repair learning</div>
          <div>
            Operation: <strong>{String(repairLearning.operation ?? "unknown").replace(/_/g, " ")}</strong> attempted
          </div>
          <div>
            Result: <strong>{repairLearning.helped ? "helped / resolved" : "did not resolve"}</strong>
          </div>
          {repairLearning.lesson ? <div style={{ marginTop: 4 }}>{repairLearning.lesson}</div> : null}
          {repairLearning.recommended_next_action ? (
            <div style={{ marginTop: 4 }}>
              Recommended next action: {repairLearning.recommended_next_action}
            </div>
          ) : null}
          {repairLearning.avoid_repeat_restart ? (
            <div style={{ marginTop: 4 }}>Avoid repeat restart until root cause confirmed</div>
          ) : null}
        </div>
      ) : null}
      {isReadonlyExecutionJob(job) && (
        <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>
          {readonlyExecutionBadge(job)}
          {typeof job.params?.auth_method_label === "string"
            ? ` · Auth: ${job.params.auth_method_label}`
            : ""}
          {executionDataSourceLabel(job) ? ` · ${executionDataSourceLabel(job)}` : ""}
          {executionConfidenceLabel(job) ? ` · Failure confidence: ${executionConfidenceLabel(job)}` : ""}
          {productionImpactLabel(job) ? ` · Production impact: ${productionImpactLabel(job)}` : ""}
          {typeof job.params?.operation_type === "string"
            ? ` · Operation: ${String(job.params.operation_type).replace(/_/g, " ")}`
            : ""}
        </div>
      )}
      {isReadonlyExecutionJob(job) && (() => {
        const tiers = executionEvidenceByTier(job);
        const tierKeys = ["primary", "supporting", "historical"] as const;
        const hasTiered = tierKeys.some((k) => (tiers[k]?.length ?? 0) > 0);
        const flat = executionEvidenceFromJob(job);
        if (!hasTiered && flat.length === 0) return null;
        const evidenceTitle = providerEvidenceSectionTitle(orchestrationProvider, orchestrationOperation);
        return (
          <details style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-text)" }}>
            <summary style={{ cursor: "pointer", color: "var(--aethos-text-muted)" }}>
              {evidenceTitle}
              {formatExecutionDebugEvidenceLabel(job)
                ? ` (${formatExecutionEvidenceLabel(job)} · ${formatExecutionDebugEvidenceLabel(job)} in debug)`
                : formatExecutionEvidenceLabel(job)
                  ? ` (${formatExecutionEvidenceLabel(job)})`
                  : flat.length > 0
                    ? ` (${flat.length})`
                    : ""}
            </summary>
            {hasTiered ? (
              tierKeys.map((tier) => {
                const items = tiers[tier] ?? [];
                if (items.length === 0) return null;
                return (
                  <div key={tier} style={{ marginTop: 6 }}>
                    <div style={{ color: "var(--aethos-text-muted)", fontWeight: 600, textTransform: "capitalize" }}>
                      {tier} ({items.length})
                    </div>
                    <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                      {items.slice(0, 6).map((item, i) => (
                        <li key={`${tier}-${item.type ?? "evidence"}-${i}`}>
                          {formatProviderEvidenceItem(orchestrationProvider, item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })
            ) : (
              <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                {flat.slice(0, 8).map((item, i) => (
                  <li key={`${item.type ?? "evidence"}-${i}`}>
                    {formatProviderEvidenceItem(orchestrationProvider, item)}
                  </li>
                ))}
              </ul>
            )}
            {(tiers.debug?.length ?? 0) > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary style={{ cursor: "pointer", color: "var(--aethos-text-dim)" }}>
                  Debug records ({tiers.debug!.length})
                </summary>
                <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                  {tiers.debug!.slice(0, 12).map((item, i) => (
                    <li key={`debug-${item.type ?? "evidence"}-${i}`}>
                      {formatProviderEvidenceItem(orchestrationProvider, item)}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </details>
        );
      })()}
      {isReadonlyExecutionJob(job) && executionOperationalEventsFromJob(job).length > 0 && (
        <details style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-text)" }}>
          <summary style={{ cursor: "pointer", color: "var(--aethos-text-muted)" }}>Operational events</summary>
          <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
            {executionOperationalEventsFromJob(job).slice(0, 10).map((entry, i) => (
              <li key={`${entry.label ?? "event"}-${i}`}>
                {entry.at ? `${formatOperationalEventAt(entry.at)} · ` : ""}
                {entry.label ?? entry.message ?? ""}
              </li>
            ))}
          </ul>
        </details>
      )}
      {isReadonlyExecutionJob(job) && execTimeline.length > 0 && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(134,239,172,0.25)",
            background: "rgba(134,239,172,0.06)",
            fontSize: 12,
            color: "var(--aethos-text)",
            lineHeight: 1.55,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Execution timeline</div>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {execTimeline.map((entry, i) => (
              <li key={`${entry.status ?? "step"}-${i}`}>
                {entry.status ? `[${entry.status}] ` : ""}
                {entry.message ?? ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {memoryFallback && (
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-warn)" }}>
          Memory fallback — projects may be stale until the next successful inspection.
        </p>
      )}
      {vercelInv && (vercelInv.projects?.length ?? 0) > 0 && (
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-text)" }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            {memoryFallback ? "Known projects (memory)" : "Projects"}
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
            {(vercelInv.projects ?? []).slice(0, 12).map((p) => (
              <li key={p.name}>
                <strong>{p.name}</strong>
                {p.health === "unknown"
                  ? " · production status unclear"
                  : p.health
                    ? ` · ${p.health.replace(/_/g, " ")}`
                    : ""}
                {p.production_url ? ` · ${p.production_url}` : ""}
                {p.attention_reason ? ` — ${p.attention_reason}` : ""}
                {!p.attention_reason && p.deployment_state ? ` · ${p.deployment_state}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {vercelInv && (vercelInv.projects?.length ?? 0) === 0 && summary && (
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-warn)", lineHeight: 1.5 }}>
          {summary.length > 320 ? `${summary.slice(0, 320)}…` : summary}
        </p>
      )}
      {preview && !vercelInv?.projects?.length && !summary?.includes("could not") && (
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          Preview: {preview.length > 160 ? `${preview.slice(0, 160)}…` : preview}
        </p>
      )}
      <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 }}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          style={artifactButtonStyle("var(--aethos-text)")}
        >
          {open ? "Hide full report" : "Open full report"}
        </button>
        {full && (
          <>
            <button type="button" onClick={() => void handleCopy()} style={artifactButtonStyle("var(--aethos-ok)")}>
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              type="button"
              onClick={() => downloadArtifactMarkdown(job)}
              style={artifactButtonStyle("var(--aethos-accent)")}
            >
              Download
            </button>
          </>
        )}
      </div>
      {open && (
        <div style={{ marginTop: 12 }}>
          {summary && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text)", marginBottom: 4 }}>Summary</div>
              <pre style={{ ...artifactReportPreStyle, color: "var(--aethos-text)" }}>{summary}</pre>
            </div>
          )}
          {(reportMain || full) && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text)", marginBottom: 4 }}>
                Structured report
              </div>
              <pre
                data-mc-artifact-report=""
                style={{ ...artifactReportPreStyle, color: "var(--aethos-ok)" }}
              >
                {reportMain || full}
              </pre>
            </div>
          )}
          {extractionDebug && (
            <details style={{ marginTop: 12 }}>
              <summary style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text-muted)", cursor: "pointer" }}>
                Extraction debug (pipeline + candidates)
              </summary>
              <pre
                style={{
                  ...artifactReportPreStyle,
                  color: "var(--aethos-text-dim)",
                  marginTop: 8,
                  maxHeight: 280,
                  overflow: "auto",
                }}
              >
                {extractionDebug}
              </pre>
            </details>
          )}
          {reportDebug && (
            <details
              style={{ marginTop: 12 }}
              open={debugOpen}
              onToggle={(e) => setDebugOpen((e.target as HTMLDetailsElement).open)}
            >
              <summary style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text-muted)", cursor: "pointer" }}>
                Debug extraction (raw page text)
              </summary>
              <pre
                style={{
                  ...artifactReportPreStyle,
                  color: "var(--aethos-text-dim)",
                  marginTop: 8,
                  maxHeight: 280,
                  overflow: "auto",
                }}
              >
                {reportDebug}
              </pre>
            </details>
          )}
        </div>
      )}
    </li>
  );
}

function artifactButtonStyle(color: string): CSSProperties {
  return {
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.15)",
    background: "rgba(255,255,255,0.06)",
    color,
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
  };
}

function JobList({
  title,
  items,
  showCancel,
  onCancel,
  cancellingId,
  expandableCompleted,
  expandableJob,
  onRefresh,
}: {
  title: string;
  items: TrackedJobRecord[];
  showCancel?: boolean;
  onCancel?: (id: string) => void;
  cancellingId: string | null;
  expandableCompleted?: boolean;
  expandableJob?: (job: TrackedJobRecord) => boolean;
  onRefresh?: () => void;
}) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600, color: "var(--aethos-text)" }}>{title}</h3>
      <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((j) =>
          (expandableJob?.(j) ?? (expandableCompleted && j.status === "completed")) ? (
            <CompletedJobRow key={j.id} job={j} onRefresh={onRefresh ?? (() => undefined)} />
          ) : (
            <li
              key={j.id}
              id={mcJobAnchorId(j.id)}
              style={{
                padding: 12,
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.03)",
                fontSize: 13,
              }}
            >
              <div style={{ fontWeight: 600 }}>{j.title}</div>
              <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
                {jobControlHint(j.status)} · {j.job_type} · <code>{j.id}</code>
              </div>
              {j.failure_reason && (
                <pre style={{ marginTop: 8, whiteSpace: "pre-wrap", fontSize: 12, color: "var(--aethos-danger)" }}>
                  {j.failure_reason}
                </pre>
              )}
              {showCancel && onCancel && (
                <button
                  type="button"
                  onClick={() => onCancel(j.id)}
                  disabled={cancellingId === j.id}
                  style={{
                    marginTop: 8,
                    borderRadius: 8,
                    border: "1px solid rgba(251,191,36,0.35)",
                    background: "rgba(251,191,36,0.1)",
                    color: "var(--aethos-text)",
                    padding: "6px 12px",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {cancellingId === j.id ? "Cancelling…" : "Cancel"}
                </button>
              )}
            </li>
          ),
        )}
      </ul>
    </div>
  );
}

export function JobsTrackedWorkPanel({ jobs, onRefresh, mode = "all" }: Props) {
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [panelError, setPanelError] = useState("");

  const handleCancel = useCallback(
    async (id: string) => {
      setCancellingId(id);
      setPanelError("");
      try {
        await cancelTrackedJob(id);
        onRefresh();
      } catch (e) {
        setPanelError(formatMcPanelError(e instanceof Error ? e.message : "Cancel failed"));
      } finally {
        setCancellingId(null);
      }
    },
    [onRefresh],
  );

  const grouped = normalizeJobsGrouped(jobs);
  const { readonlyExecutions, withoutReadonlyExecutions } = partitionGroupedJobs(grouped);
  const completedPreflights = partitionCompletedJobs(withoutReadonlyExecutions.completed).operationPreflights;
  const completedTrackedRaw = partitionCompletedJobs(withoutReadonlyExecutions.completed).trackedWork;
  const mutationPartition = partitionMutationJobs(completedTrackedRaw);
  const currentMutationPreflights = mutationPartition.mutationPreflights.filter(isCurrentMutationPreflight);
  const previousMutationPreflights = mutationPartition.mutationPreflights.filter((j) => !isCurrentMutationPreflight(j));
  const completedTracked = [
    ...mutationPartition.other,
    ...mutationPartition.mutationExecutions,
  ];
  const { current: currentPreflights, previous: previousPreflights } =
    partitionPreflights(completedPreflights);
  const empty =
    grouped.queued.length +
      grouped.running.length +
      grouped.completed.length +
      grouped.failed.length +
      grouped.cancelled.length ===
    0;

  const showPreflights = mode === "all" || mode === "preflights";
  const showTrackedLists = mode === "all" || mode === "tracked";

  return (
    <div style={{ marginTop: 24 }}>
      <h2 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>Tracked work</h2>
      <p style={{ margin: "0 0 12px", fontSize: 13, color: "var(--aethos-text-muted)" }}>
        Full reports live here — chat shows lifecycle and short summaries only. Queued jobs can be{" "}
        <strong>cancelled</strong>.
      </p>

      {panelError && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 13, marginBottom: 12 }} role="status">
          {panelError}
        </p>
      )}

      {empty && (
        <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>
          No tracked jobs yet. Try: “research the top competitors to AethOS”.
        </p>
      )}

      {showTrackedLists && (
        <>
      <JobList
        title="Queued"
        items={withoutReadonlyExecutions.queued}
        showCancel
        onCancel={handleCancel}
        cancellingId={cancellingId}
      />
      {!readonlyExecutionsEmpty(readonlyExecutions) && (
        <>
          <JobList
            title="Read-only executions — queued"
            items={readonlyExecutions.queued}
            cancellingId={null}
            expandableJob={isReadonlyExecutionJob}
            onRefresh={onRefresh}
          />
          <JobList
            title="Read-only executions — running"
            items={readonlyExecutions.running}
            cancellingId={null}
            expandableJob={isReadonlyExecutionJob}
            onRefresh={onRefresh}
          />
          <JobList
            title="Read-only executions"
            items={readonlyExecutions.completed}
            cancellingId={null}
            expandableJob={isReadonlyExecutionJob}
            onRefresh={onRefresh}
          />
          <JobList
            title="Read-only executions — failed"
            items={readonlyExecutions.failed}
            cancellingId={null}
            expandableJob={isReadonlyExecutionJob}
            onRefresh={onRefresh}
          />
        </>
      )}
        </>
      )}
      {showPreflights && currentMutationPreflights.length > 0 && (
        <JobList
          title="Mutation preflights"
          items={currentMutationPreflights}
          cancellingId={null}
          expandableCompleted
          onRefresh={onRefresh}
        />
      )}
      {showPreflights && previousMutationPreflights.length > 0 && (
        <JobList
          title="Previous mutation attempts"
          items={previousMutationPreflights}
          cancellingId={null}
          expandableCompleted
          onRefresh={onRefresh}
        />
      )}
      {showPreflights && currentPreflights.length > 0 && (
        <JobList
          title="Operation preflights"
          items={currentPreflights}
          cancellingId={null}
          expandableCompleted
          onRefresh={onRefresh}
        />
      )}
      {showPreflights && previousPreflights.length > 0 && (
        <JobList
          title="Previous preflight attempts"
          items={previousPreflights}
          cancellingId={null}
          expandableCompleted
          onRefresh={onRefresh}
        />
      )}
      {showTrackedLists && (
        <>
      <JobList title="Running" items={withoutReadonlyExecutions.running} cancellingId={null} />
      <JobList
        title="Tracked work"
        items={completedTracked}
        cancellingId={null}
        expandableCompleted
        onRefresh={onRefresh}
      />
      <JobList title="Failed" items={withoutReadonlyExecutions.failed} cancellingId={null} />
      <JobList title="Cancelled" items={withoutReadonlyExecutions.cancelled} cancellingId={null} />
        </>
      )}
    </div>
  );
}
