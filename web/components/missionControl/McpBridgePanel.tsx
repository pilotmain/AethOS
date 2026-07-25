"use client";

import { useCallback, useEffect, useState } from "react";

import Link from "next/link";

import {
  fetchMcpTools,
  invokeMcpTool,
  type McpInvokeResult,
  type McpToolSummary,
} from "@/lib/missionControl/mcpBridgeApi";
import { mcButtonPrimaryStyle, mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

const card = {
  padding: "14px 16px",
  borderRadius: 14,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.22)",
  marginBottom: 12,
} as const;

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function McpBridgePanel() {
  const [catalog, setCatalog] = useState<Awaited<ReturnType<typeof fetchMcpTools>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lastResult, setLastResult] = useState<McpInvokeResult | null>(null);
  const [chatText, setChatText] = useState("");
  const [chatSessionId, setChatSessionId] = useState("default");

  const load = useCallback(async () => {
    try {
      setError(null);
      setCatalog(await fetchMcpTools());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load MCP catalog");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const runTool = async (tool: McpToolSummary) => {
    setBusy(true);
    setError(null);
    try {
      let args: Record<string, unknown> = {};
      if (tool.name === "aethos_chat_turn") {
        const text = chatText.trim();
        if (!text) {
          setError("Enter chat text for aethos_chat_turn.");
          setBusy(false);
          return;
        }
        args = { text, session_id: chatSessionId.trim() || "default" };
      }
      const result = await invokeMcpTool(tool.name, args);
      setLastResult(result);
      if (!result.ok) setError(result.error || "Invoke failed");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invoke failed");
    } finally {
      setBusy(false);
    }
  };

  const readonlyTools = (catalog?.tools ?? []).filter((t) => t.readonly !== false);
  const mutationTools = (catalog?.tools ?? []).filter((t) => t.readonly === false);

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>MCP Bridge</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
            Governed operator tools exposed through the MCP bridge — readonly diagnostics and chat turns.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle} disabled={busy}>
          Refresh
        </button>
      </div>

      <div style={{ ...card, marginTop: 16, borderColor: catalog?.enabled ? mcColors.green : mcColors.amber }}>
        <div style={{ fontWeight: 600, fontSize: 14 }}>
          Bridge {catalog?.enabled ? "enabled" : "disabled"}
        </div>
        {!catalog?.enabled ? (
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.amber }}>
            Set `MCP_BRIDGE_ENABLED=true` and restart the API to allow invoke. Catalog remains readable.
          </p>
        ) : null}
        <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
          Local skills browser: <Link href="/skills" style={{ color: mcColors.cyan }}>/skills</Link>
        </p>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 12 }}>{error}</p> : null}

      <div style={card}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Readonly tools</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {readonlyTools.map((tool) => (
            <button
              key={tool.name}
              type="button"
              disabled={busy || !catalog?.enabled}
              style={mcButtonSecondaryStyle}
              onClick={() => void runTool(tool)}
            >
              {tool.name}
            </button>
          ))}
        </div>
        {readonlyTools.length === 0 ? (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>No readonly tools in catalog.</p>
        ) : null}
      </div>

      {mutationTools.length > 0 ? (
        <div style={card}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Governed chat turn</div>
          <textarea
            value={chatText}
            onChange={(e) => setChatText(e.target.value)}
            placeholder="Operator message for aethos_chat_turn…"
            rows={3}
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "10px 12px",
              borderRadius: 10,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.35)",
              color: mcColors.text,
              fontSize: 13,
              marginBottom: 8,
            }}
          />
          <input
            value={chatSessionId}
            onChange={(e) => setChatSessionId(e.target.value)}
            placeholder="session_id"
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "8px 10px",
              borderRadius: 8,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.35)",
              color: mcColors.text,
              fontSize: 12,
              marginBottom: 10,
            }}
          />
          <button
            type="button"
            style={mcButtonPrimaryStyle}
            disabled={busy || !catalog?.enabled}
            onClick={() => void runTool(mutationTools[0]!)}
          >
            Run aethos_chat_turn
          </button>
        </div>
      ) : null}

      {lastResult ? (
        <div style={card}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>
            Last result {lastResult.tool ? `· ${lastResult.tool}` : ""}
          </div>
          <pre
            style={{
              margin: 0,
              padding: 12,
              borderRadius: 10,
              background: "rgba(0,0,0,0.35)",
              fontSize: 11,
              lineHeight: 1.45,
              overflow: "auto",
              maxHeight: 420,
              color: mcColors.textMuted,
            }}
          >
            {formatJson(lastResult.result ?? lastResult)}
          </pre>
        </div>
      ) : null}
    </section>
  );
}
