"use client";

import {
  isCurrentMutationPreflight,
  partitionMutationJobs,
} from "@/lib/missionControl/mutationArtifacts";
import { partitionMutationAuditRecords } from "@/lib/missionControl/mutationAudit";
import {
  mcJobAnchorId,
  partitionCompletedJobs,
  partitionGroupedJobs,
} from "@/lib/missionControl/operationPreflight";
import { mcPanelSectionStyle, mcColors } from "@/lib/missionControl/layout";
import type { JobsGrouped } from "@/lib/missionControl/trackedJobs";
import { normalizeJobsGrouped } from "@/lib/missionControl/trackedJobs";

type Props = {
  jobs: JobsGrouped;
};

export function MutationAuditPanel({ jobs }: Props) {
  const grouped = normalizeJobsGrouped(jobs);
  const { withoutReadonlyExecutions } = partitionGroupedJobs(grouped);
  const completedPreflights = partitionCompletedJobs(withoutReadonlyExecutions.completed).operationPreflights;
  const completedTrackedRaw = partitionCompletedJobs(withoutReadonlyExecutions.completed).trackedWork;
  const mutationPartition = partitionMutationJobs(completedTrackedRaw);
  const currentMutationPreflights = mutationPartition.mutationPreflights.filter(isCurrentMutationPreflight);
  const previousMutationPreflights = mutationPartition.mutationPreflights.filter((j) => !isCurrentMutationPreflight(j));
  const mutationAuditPartition = partitionMutationAuditRecords([
    ...currentMutationPreflights,
    ...previousMutationPreflights,
    ...mutationPartition.mutationExecutions,
    ...completedTrackedRaw,
  ]);

  if (mutationAuditPartition.current.length === 0 && mutationAuditPartition.historical.length === 0) {
    return (
      <section style={mcPanelSectionStyle}>
        <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Mutation Audit</h2>
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
          No governed mutation chains yet. Preflight → approval → execution → verification → audit.
        </p>
      </section>
    );
  }

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Mutation Audit</h2>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: mcColors.textMuted }}>
        Current governed mutation chains — preflight → approval → execution → verification → audit.
      </p>

      {mutationAuditPartition.current.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ margin: "0 0 10px", fontSize: 14, fontWeight: 600, color: "var(--aethos-danger)" }}>
            Active chains ({mutationAuditPartition.current.length})
          </h3>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
            {mutationAuditPartition.current.slice(0, 12).map((record) => (
              <li
                key={record.chainId}
                style={{
                  marginBottom: 12,
                  padding: "14px 16px",
                  borderRadius: 12,
                  border: `1px solid ${mcColors.border}`,
                  background: "rgba(0,0,0,0.25)",
                }}
              >
                <div style={{ color: "var(--aethos-danger)", fontWeight: 600, fontSize: 14 }}>
                  {record.provider} · {record.operation.replace(/_/g, " ")}
                  {record.target ? ` · ${record.target}` : ""}
                </div>
                {record.evidenceTitle ? (
                  <div style={{ color: mcColors.textMuted, marginTop: 6 }}>{record.evidenceTitle}</div>
                ) : null}
                <div style={{ color: mcColors.text, marginTop: 8, lineHeight: 1.6 }}>
                  {record.steps.map((step, i) => (
                    <span key={step.key}>
                      {i > 0 ? " → " : ""}
                      {step.jobId ? (
                        <a href={`#${mcJobAnchorId(step.jobId)}`} style={{ color: "var(--aethos-danger)" }}>
                          {step.label}
                        </a>
                      ) : (
                        step.label
                      )}
                      {step.status ? ` (${step.status.replace(/_/g, " ")})` : ""}
                    </span>
                  ))}
                </div>
                {record.lifecycleSummary ? (
                  <div style={{ color: mcColors.textDim, marginTop: 8, fontSize: 12 }}>
                    {record.lifecycleSummary}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      )}

      {mutationAuditPartition.historical.length > 0 && (
        <details style={{ fontSize: 13, color: mcColors.textMuted }}>
          <summary style={{ cursor: "pointer", fontWeight: 600, color: mcColors.text }}>
            Previous attempts ({mutationAuditPartition.historical.length})
          </summary>
          <ul style={{ margin: "12px 0 0", padding: 0, listStyle: "none" }}>
            {mutationAuditPartition.historical.slice(0, 16).map((record) => (
              <li
                key={`hist-${record.chainId}`}
                style={{
                  marginBottom: 8,
                  padding: "10px 12px",
                  borderRadius: 10,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  opacity: 0.9,
                }}
              >
                <div style={{ color: mcColors.text }}>
                  {record.provider} · {record.operation.replace(/_/g, " ")}
                  {record.target ? ` · ${record.target}` : ""}
                </div>
                {record.lifecycleSummary ? (
                  <div style={{ color: mcColors.textDim, marginTop: 4, fontSize: 12 }}>
                    {record.lifecycleSummary}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
