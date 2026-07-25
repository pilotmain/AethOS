"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchCronStatus } from "@/lib/missionControl/phase4Api";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function CronGovernedJobsPanel() {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchCronStatus>>>(null);

  const load = useCallback(async () => {
    setData(await fetchCronStatus());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const jobs = (data?.recent_observation_jobs as { id?: string; title?: string; status?: string }[]) ?? [];

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Cron & governed jobs</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Observation cycles enqueue durable jobs when `CRON_GOVERNED_JOBS_ENABLED=true`.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>
      <p style={{ marginTop: 14, fontSize: 13, color: data?.enabled ? mcColors.green : mcColors.amber }}>
        Bridge {data?.enabled ? "enabled" : "disabled"}
      </p>
      {jobs.length === 0 ? (
        <p style={{ fontSize: 12, color: mcColors.textMuted }}>No recent observation jobs.</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
          {jobs.map((job) => (
            <li key={job.id} style={{ padding: "8px 0", borderBottom: `1px solid ${mcColors.borderSubtle}` }}>
              {job.title} · {job.status}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
