"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { downloadTextFile } from "@/lib/missionControl/missionControlEvidenceBundleApi";
import {
  fetchMissionControlJobReplay,
  jobReplaySummaryFilename,
  type JobReplayPayload,
  type JobReplayStep,
} from "@/lib/missionControl/missionControlJobReplayApi";
import { fetchMissionControlRerunPlan } from "@/lib/missionControl/missionControlRerunPlanApi";
import { resolveMissionControlJobReplayLink } from "@/lib/missionControl/missionControlJobReplayResolveApi";
import {
  readOperatorUrlState,
  writeOperatorUrlState,
  type ReplayDeepLinkTarget,
} from "@/lib/missionControl/missionControlReplayDeepLink";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { buildOperatorContext, useOperatorSession, type OperatorContext } from "@/lib/missionControl/operatorSession";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

type Props = {
  sessionId?: string;
  operatorMode?: MissionControlMode;
  deepLinkTarget?: ReplayDeepLinkTarget | null;
  onDeepLinkConsumed?: () => void;
};

function resolveInitialStep(replay: JobReplayPayload, target: ReplayDeepLinkTarget | null | undefined): number {
  if (!replay.steps.length) return 0;
  if (target?.stepIndex != null && target.stepIndex >= 0 && target.stepIndex < replay.steps.length) {
    return target.stepIndex;
  }
  const link = target?.link ?? target?.linkRef ?? target?.linkKey;
  if (link && replay.link_index && replay.link_index[link] != null) {
    return replay.link_index[link];
  }
  if (link) {
    for (const step of replay.steps) {
      if (step.link_key === link) return step.step_index;
      const refs = step.link_refs ?? {};
      if (Object.values(refs).includes(link)) return step.step_index;
    }
  }
  return 0;
}

type LoadState = "idle" | "loading" | "loaded" | "error";

export function JobReplayPanel({
  sessionId: sessionIdProp,
  operatorMode = "operator",
  deepLinkTarget,
  onDeepLinkConsumed,
}: Props) {
  const { context: operatorContext, hydrated } = useOperatorSession(sessionIdProp);
  const sessionId = operatorContext?.sessionId ?? sessionIdProp ?? "default";
  const operatorCtx = useMemo(
    () => operatorContext ?? buildOperatorContext(sessionId, operatorMode),
    [operatorContext, sessionId, operatorMode],
  );

  const [jobIdFocus, setJobIdFocus] = useState("");
  const [replaySteps, setReplaySteps] = useState<JobReplayStep[]>([]);
  const [missionMeta, setMissionMeta] = useState<Record<string, unknown> | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [rerunPlanMd, setRerunPlanMd] = useState<string | null>(null);
  const [rerunPlanLoading, setRerunPlanLoading] = useState(false);

  const pendingDeepLink = useMemo(() => {
    const url = readOperatorUrlState();
    return deepLinkTarget ?? {
      link: url.link,
      linkRef: url.linkRef,
      linkKey: url.linkKey,
      stepIndex: url.stepIndex,
      jobId: url.jobId,
    };
  }, [deepLinkTarget]);

  useEffect(() => {
    if (pendingDeepLink.jobId && !jobIdFocus) {
      setJobIdFocus(pendingDeepLink.jobId);
    }
  }, [pendingDeepLink.jobId, jobIdFocus]);

  const load = useCallback(async () => {
    if (!hydrated) return;
    try {
      setLoadState("loading");
      setErrorMessage(null);
      const focus = (pendingDeepLink.jobId ?? jobIdFocus).trim() || undefined;
      const res = await fetchMissionControlJobReplay(sessionId, "both", focus);
      const replay = res.replay;
      const steps = replay?.steps ?? [];
      let stepIdx = replay ? resolveInitialStep(replay, pendingDeepLink) : 0;
      const link = pendingDeepLink.link ?? pendingDeepLink.linkRef ?? pendingDeepLink.linkKey;
      if (link && replay && replay.link_index?.[link] == null) {
        try {
          const resolved = await resolveMissionControlJobReplayLink(sessionId, link, focus);
          if (resolved.ok && resolved.step_index != null) stepIdx = resolved.step_index;
        } catch {
          /* keep default step */
        }
      }
      setReplaySteps(steps);
      setMissionMeta(replay?.mission ?? null);
      setActiveStep(steps.length ? stepIdx : 0);
      setLoadState("loaded");
      onDeepLinkConsumed?.();
      writeOperatorUrlState({
        view: "mission-job-replay",
        stepIndex: steps.length ? stepIdx : 0,
        link: link ?? steps[stepIdx]?.link_key,
        jobId: focus,
      });
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : "Failed to load job replay");
      setReplaySteps([]);
      setLoadState("error");
    }
  }, [hydrated, sessionId, jobIdFocus, pendingDeepLink, onDeepLinkConsumed]);

  useEffect(() => {
    void load();
  }, [load]);

  const setActiveStepPersisted = useCallback(
    (index: number) => {
      setActiveStep(index);
      const step = replaySteps[index];
      writeOperatorUrlState({
        view: "mission-job-replay",
        stepIndex: index,
        link: step?.link_key ?? step?.link_refs?.timeline,
        jobId: jobIdFocus.trim() || pendingDeepLink.jobId,
      });
    },
    [replaySteps, jobIdFocus, pendingDeepLink.jobId],
  );

  const current = replaySteps[activeStep];
  const correlationId = String(missionMeta?.correlation_id ?? "");

  const handleExportSummary = useCallback(async () => {
    try {
      setExportMessage(null);
      const focus = jobIdFocus.trim() || undefined;
      const res = await fetchMissionControlJobReplay(sessionId, "summary", focus);
      if (!res.summary_markdown) {
        setExportMessage("No replay summary returned.");
        return;
      }
      downloadTextFile(
        res.summary_markdown,
        jobReplaySummaryFilename(sessionId, correlationId),
        "text/markdown;charset=utf-8",
      );
      setExportMessage("Replay summary downloaded.");
    } catch (e) {
      setExportMessage(e instanceof Error ? e.message : "Export failed");
    }
  }, [sessionId, jobIdFocus, correlationId]);

  const handleShowRerunPlan = useCallback(async () => {
    try {
      setRerunPlanLoading(true);
      setRerunPlanMd(null);
      const focus = jobIdFocus.trim() || undefined;
      const step = replaySteps[activeStep];
      const res = await fetchMissionControlRerunPlan(sessionId, "markdown", {
        jobId: focus,
        fromStep: activeStep,
        linkKey: step?.link_key,
      });
      setRerunPlanMd(res.markdown ?? "No rerun plan returned.");
    } catch (e) {
      setRerunPlanMd(e instanceof Error ? e.message : "Failed to load governed rerun plan");
    } finally {
      setRerunPlanLoading(false);
    }
  }, [sessionId, jobIdFocus, replaySteps, activeStep]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <section style={mcPanelSectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
          <div>
            <h2 style={{ margin: "0 0 6px", fontSize: 20, fontWeight: 600 }}>Job replay</h2>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              Read-only step-by-step playback from evidence bundle data — understand how the mission reached its
              current state. No rerun or mutation controls.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
            <ReadOnlyBadge />
            <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()} disabled={loadState === "loading"}>
              Refresh replay
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleExportSummary()}
              disabled={loadState !== "loaded" || replaySteps.length === 0}
            >
              Export replay summary
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleShowRerunPlan()}
              disabled={loadState !== "loaded" || replaySteps.length === 0 || rerunPlanLoading}
              title="Planning only — does not execute a rerun"
            >
              {rerunPlanLoading ? "Planning…" : "Show governed rerun plan"}
            </button>
          </div>
        </div>

        {!hydrated ? null : <OperatorContextBar context={operatorCtx} mission={missionMeta} stepCount={replaySteps.length} />}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <label style={{ fontSize: 12, color: mcColors.textMuted }}>
            Optional job focus
            <input
              value={jobIdFocus}
              onChange={(e) => setJobIdFocus(e.target.value)}
              placeholder="job-…"
              style={{
                marginLeft: 8,
                padding: "6px 8px",
                borderRadius: 6,
                border: `1px solid ${mcColors.border}`,
                background: mcColors.bgElevated,
                color: mcColors.text,
                fontSize: 12,
                minWidth: 180,
              }}
            />
          </label>
        </div>

        {loadState === "loading" ? (
          <p style={{ marginTop: 12, fontSize: 13, color: mcColors.textMuted }}>Building replay from evidence bundle…</p>
        ) : null}
        {errorMessage ? (
          <p style={{ marginTop: 12, fontSize: 13, color: mcColors.amber }}>{errorMessage}</p>
        ) : null}
        {exportMessage ? <p style={{ marginTop: 8, fontSize: 12, color: mcColors.textMuted }}>{exportMessage}</p> : null}

        {loadState === "loaded" && replaySteps.length > 0 ? (
          <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "minmax(220px, 280px) 1fr", gap: 16 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {replaySteps.map((step, index) => (
                <button
                  key={step.step_id}
                  type="button"
                  onClick={() => setActiveStepPersisted(index)}
                  style={{
                    textAlign: "left",
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: `1px solid ${index === activeStep ? mcColors.cyan : mcColors.border}`,
                    background: index === activeStep ? "rgba(56, 189, 248, 0.08)" : mcColors.bgElevated,
                    color: mcColors.text,
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>Step {index + 1}</div>
                  <div style={{ color: mcColors.textMuted }}>{step.action}</div>
                </button>
              ))}
            </div>

            {current ? (
              <StepDetail
                step={current}
                index={activeStep}
                total={replaySteps.length}
                onStep={setActiveStepPersisted}
                linkKey={current.link_key}
              />
            ) : null}
          </div>
        ) : null}

        {loadState === "loaded" && replaySteps.length === 0 ? (
          <p style={{ marginTop: 12, fontSize: 13, color: mcColors.textMuted }}>
            No replay steps yet for this session. Run a software delivery workflow or tracked job to populate timeline
            data.
          </p>
        ) : null}

        {rerunPlanMd ? (
          <section
            style={{
              marginTop: 16,
              padding: 12,
              borderRadius: 10,
              border: `1px solid ${mcColors.border}`,
              background: "rgba(0,0,0,0.2)",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>Governed rerun plan (preview)</h3>
            <p style={{ margin: "0 0 10px", fontSize: 12, color: mcColors.textMuted }}>
              Answers “if we rerun this flow, what would happen?” — planning only. No rerun execution in FIX 138.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                maxHeight: 360,
                overflow: "auto",
                color: mcColors.textMuted,
              }}
            >
              {rerunPlanMd}
            </pre>
          </section>
        ) : null}
      </section>
    </div>
  );
}

function StepDetail({
  step,
  index,
  total,
  onStep,
  linkKey,
}: {
  step: JobReplayStep;
  index: number;
  total: number;
  onStep: (n: number) => void;
  linkKey?: string;
}) {
  return (
    <div style={{ border: `1px solid ${mcColors.border}`, borderRadius: 10, padding: 14, background: mcColors.bgElevated }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ fontSize: 14, fontWeight: 600 }}>
          Step {index + 1} / {total}: {step.action}
          {linkKey ? (
            <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 400, color: mcColors.textDim, fontFamily: "monospace" }}>
              {linkKey}
            </span>
          ) : null}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            disabled={index <= 0}
            onClick={() => onStep(index - 1)}
          >
            Previous step
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            disabled={index >= total - 1}
            onClick={() => onStep(index + 1)}
          >
            Next step
          </button>
        </div>
      </div>
      <MetaRow label="Lane" value={step.lane ?? "—"} />
      <MetaRow label="Source" value={step.source ?? "—"} />
      <MetaRow label="Timestamp" value={step.timestamp ?? "—"} mono />
      <MetaRow label="Detail" value={step.detail ?? "—"} />

      <Section title="State before">
        <StateBlock state={step.state_before} />
      </Section>
      <Section title="State after">
        <StateBlock state={step.state_after} />
      </Section>
      <Section title="Gates">
        <ItemList items={step.gates} labelKey="gate" />
      </Section>
      <Section title="Receipts">
        <ItemList items={step.receipts} labelKey="detail" fallbackKey="phase" />
      </Section>
      <Section title="Blockers at transition">
        <ItemList items={step.blockers} labelKey="detail" fallbackKey="gate" />
      </Section>
      <Section title="Approvals at transition">
        <ItemList items={step.approvals} labelKey="gate" fallbackKey="status" />
      </Section>
    </div>
  );
}

function StateBlock({ state }: { state?: Record<string, unknown> }) {
  if (!state) return <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>—</p>;
  return (
    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: mcColors.textMuted }}>
      <li>plan_status: {String(state.plan_status ?? "—")}</li>
      <li>gates_passed: {(state.gates_passed as string[] | undefined)?.join(", ") || "none"}</li>
      <li>pending_gates: {(state.pending_gates as string[] | undefined)?.join(", ") || "none"}</li>
    </ul>
  );
}

function ItemList({
  items,
  labelKey,
  fallbackKey,
}: {
  items?: Array<Record<string, unknown>>;
  labelKey: string;
  fallbackKey?: string;
}) {
  if (!items?.length) {
    return <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>None at this step.</p>;
  }
  return (
    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: mcColors.textMuted }}>
      {items.slice(0, 8).map((item, i) => (
        <li key={i}>{String(item[labelKey] ?? (fallbackKey ? item[fallbackKey] : "") ?? "record")}</li>
      ))}
    </ul>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: mcColors.text, marginBottom: 4 }}>{title}</div>
      {children}
    </div>
  );
}

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ fontSize: 12, marginBottom: 4 }}>
      <span style={{ color: mcColors.textMuted }}>{label}: </span>
      <span style={mono ? { fontFamily: "monospace", color: mcColors.cyan } : undefined}>{value}</span>
    </div>
  );
}

function ReadOnlyBadge() {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        color: mcColors.cyan,
        border: `1px solid ${mcColors.cyanDim}`,
        borderRadius: 6,
        padding: "4px 8px",
      }}
    >
      Read-only replay
    </span>
  );
}

function OperatorContextBar({
  context,
  mission,
  stepCount,
}: {
  context: OperatorContext;
  mission: Record<string, unknown> | null;
  stepCount: number;
}) {
  return (
    <div
      style={{
        marginTop: 12,
        padding: "10px 12px",
        borderRadius: 8,
        border: `1px solid ${mcColors.border}`,
        background: mcColors.bgElevated,
        fontSize: 12,
        display: "flex",
        flexWrap: "wrap",
        gap: 12,
      }}
    >
      <span>
        Session <code style={{ color: mcColors.cyan }}>{context.sessionId}</code>
      </span>
      <span>
        Correlation <code style={{ color: mcColors.cyan }}>{String(mission?.correlation_id ?? "—")}</code>
      </span>
      <span>
        Plan <code style={{ color: mcColors.cyan }}>{String(mission?.plan_id ?? "—")}</code>
      </span>
      <span>Steps: {stepCount}</span>
    </div>
  );
}
