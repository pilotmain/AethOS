"use client";

import { useCallback, useEffect, useState } from "react";

import {
  createScheduledTask,
  createWebhookTrigger,
  deleteScheduledTask,
  deleteWebhookTrigger,
  fetchAutomationStatus,
  fetchScheduledTasks,
  fetchWebhookTriggers,
  type ScheduledTask,
  type WebhookTrigger,
} from "@/lib/missionControl/automationApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: mcColors.bgCard,
  color: mcColors.text,
  fontSize: 13,
};

export function ProactiveAutomationPanel() {
  const [enabled, setEnabled] = useState(false);
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [triggers, setTriggers] = useState<WebhookTrigger[]>([]);
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [scheduleName, setScheduleName] = useState("Morning health summary");
  const [schedulePrompt, setSchedulePrompt] = useState("Summarize Railway deployment health in three bullets.");
  const [webhookName, setWebhookName] = useState("Deploy webhook");
  const [webhookPrompt, setWebhookPrompt] = useState("A deploy webhook fired. Summarize what to check next.");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const status = await fetchAutomationStatus();
    setEnabled(Boolean(status?.enabled));
    if (!status?.enabled) {
      setTasks([]);
      setTriggers([]);
      return;
    }
    const [sched, hooks] = await Promise.all([fetchScheduledTasks(), fetchWebhookTriggers()]);
    setTasks(sched.tasks ?? []);
    setTriggers(hooks.triggers ?? []);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onCreateSchedule = async () => {
    setError(null);
    const result = await createScheduledTask({
      name: scheduleName,
      prompt: schedulePrompt,
      schedule_kind: "interval",
      interval_sec: 3600,
      action_kind: "chat",
      delivery_channel: "web",
      delivery_target: "default",
    });
    if (!result?.ok) {
      setError(String(result?.detail ?? "Failed to create schedule"));
      return;
    }
    await load();
  };

  const onCreateWebhook = async () => {
    setError(null);
    const result = await createWebhookTrigger({
      name: webhookName,
      prompt: webhookPrompt,
      action_kind: "governed_job",
      job_type: "research_scan",
      delivery_channel: "web",
      delivery_target: "default",
      allow_mutation: false,
    });
    if (!result?.ok) {
      setError(String(result?.detail ?? "Failed to create webhook"));
      return;
    }
    const secret = result?.trigger?.secret as string | undefined;
    if (secret) setNewSecret(secret);
    await load();
  };

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Proactive automation</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Scheduled tasks and inbound webhooks run as governed jobs and deliver results to your chosen channel.
            Set `PROACTIVE_AUTOMATION_ENABLED=true` to enable.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      <p style={{ marginTop: 14, fontSize: 13, color: enabled ? mcColors.green : mcColors.amber }}>
        Automation {enabled ? "enabled" : "disabled"}
      </p>

      {error ? (
        <p style={{ fontSize: 12, color: mcColors.red }}>{error}</p>
      ) : null}

      {newSecret ? (
        <p style={{ fontSize: 12, color: mcColors.amber }}>
          New webhook secret (copy now — shown once): <code>{newSecret}</code>
        </p>
      ) : null}

      {!enabled ? null : (
        <>
          <div style={{ marginTop: 20 }}>
            <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>Create scheduled task</h3>
            <div style={{ display: "grid", gap: 8, maxWidth: 560 }}>
              <input
                aria-label="Schedule name"
                value={scheduleName}
                onChange={(e) => setScheduleName(e.target.value)}
                style={inputStyle}
              />
              <textarea
                aria-label="Schedule prompt"
                value={schedulePrompt}
                onChange={(e) => setSchedulePrompt(e.target.value)}
                rows={3}
                style={inputStyle}
              />
              <button type="button" onClick={() => void onCreateSchedule()} style={mcButtonSecondaryStyle}>
                Add hourly schedule
              </button>
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>Create webhook trigger</h3>
            <div style={{ display: "grid", gap: 8, maxWidth: 560 }}>
              <input
                aria-label="Webhook name"
                value={webhookName}
                onChange={(e) => setWebhookName(e.target.value)}
                style={inputStyle}
              />
              <textarea
                aria-label="Webhook prompt"
                value={webhookPrompt}
                onChange={(e) => setWebhookPrompt(e.target.value)}
                rows={3}
                style={inputStyle}
              />
              <button type="button" onClick={() => void onCreateWebhook()} style={mcButtonSecondaryStyle}>
                Add governed webhook (research_scan)
              </button>
            </div>
          </div>

          <div style={{ marginTop: 24, display: "grid", gap: 20, gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>Scheduled tasks</h3>
              {tasks.length === 0 ? (
                <p style={{ fontSize: 12, color: mcColors.textMuted }}>No schedules yet.</p>
              ) : (
                <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
                  {tasks.map((task) => (
                    <li
                      key={task.task_id}
                      style={{ padding: "8px 0", borderBottom: `1px solid ${mcColors.borderSubtle}` }}
                    >
                      <strong>{task.name}</strong>
                      <div style={{ color: mcColors.textMuted }}>{task.prompt.slice(0, 80)}</div>
                      <button
                        type="button"
                        style={{ ...mcButtonSecondaryStyle, marginTop: 6, fontSize: 11 }}
                        onClick={() => void deleteScheduledTask(task.task_id).then(load)}
                      >
                        Delete
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>Webhook triggers</h3>
              {triggers.length === 0 ? (
                <p style={{ fontSize: 12, color: mcColors.textMuted }}>No webhooks yet.</p>
              ) : (
                <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
                  {triggers.map((trigger) => (
                    <li
                      key={trigger.trigger_id}
                      style={{ padding: "8px 0", borderBottom: `1px solid ${mcColors.borderSubtle}` }}
                    >
                      <strong>{trigger.name}</strong>
                      <div style={{ color: mcColors.textMuted }}>{trigger.webhook_url_path}</div>
                      <button
                        type="button"
                        style={{ ...mcButtonSecondaryStyle, marginTop: 6, fontSize: 11 }}
                        onClick={() => void deleteWebhookTrigger(trigger.trigger_id).then(load)}
                      >
                        Delete
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
