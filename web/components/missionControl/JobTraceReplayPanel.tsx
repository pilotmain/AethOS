"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchJobTrace, fetchRouteTrace } from "@/lib/missionControl/productionApi";
import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type Props = {
  sessionId?: string;
  jobId?: string;
};

export function JobTraceReplayPanel({ sessionId = "default", jobId }: Props) {
  const [routeTrace, setRouteTrace] = useState<Record<string, unknown> | null>(null);
  const [jobTrace, setJobTrace] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setRouteTrace(await fetchRouteTrace(sessionId));
      if (jobId) {
        setJobTrace(await fetchJobTrace(jobId));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load trace");
    }
  }, [sessionId, jobId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const trace = (routeTrace?.trace as Record<string, unknown>) ?? null;
  const deepLink = String(routeTrace?.deep_link ?? "");

  return (
    <section style={{ ...mcPanelSectionStyle, marginTop: 16 }}>
      <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Governed job trace & replay</h2>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>
        End-to-end route metadata for session <code>{sessionId}</code>
        {jobId ? ` · job <code>${jobId}</code>` : ""}.
      </p>
      {error ? <p style={{ color: mcColors.warning, fontSize: 12 }}>{error}</p> : null}
      {trace ? (
        <pre style={{ fontSize: 11, whiteSpace: "pre-wrap", color: mcColors.textMuted }}>{JSON.stringify(trace, null, 2)}</pre>
      ) : (
        <p style={{ fontSize: 12, color: mcColors.textMuted }}>No route trace recorded for this session yet.</p>
      )}
      {deepLink ? (
        <p style={{ marginTop: 8, fontSize: 12 }}>
          Deep link: <code>{deepLink}</code>
        </p>
      ) : null}
      {jobTrace?.truth ? (
        <details style={{ marginTop: 12 }}>
          <summary style={{ cursor: "pointer", fontSize: 12 }}>Mutation job truth</summary>
          <pre style={{ fontSize: 11, whiteSpace: "pre-wrap", color: mcColors.textMuted }}>
            {JSON.stringify(jobTrace.truth, null, 2)}
          </pre>
        </details>
      ) : null}
    </section>
  );
}
