/** MCP bridge operator API. */

import { apiBase } from "@/lib/api";

export type McpToolSummary = {
  name: string;
  description?: string;
  readonly?: boolean;
};

export type McpToolCatalog = {
  ok: boolean;
  enabled: boolean;
  tools: McpToolSummary[];
};

export type McpInvokeResult = {
  ok: boolean;
  tool?: string;
  result?: unknown;
  error?: string;
};

export async function fetchMcpTools(): Promise<McpToolCatalog> {
  const res = await fetch(`${apiBase()}/api/v1/runtime/mcp/tools`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return { ok: false, enabled: false, tools: [] };
  return res.json() as Promise<McpToolCatalog>;
}

export async function invokeMcpTool(
  name: string,
  args: Record<string, unknown> = {},
): Promise<McpInvokeResult> {
  const res = await fetch(`${apiBase()}/api/v1/runtime/mcp/invoke`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ name, arguments: args }),
  });
  if (!res.ok) {
    return { ok: false, error: `invoke_failed_${res.status}` };
  }
  return res.json() as Promise<McpInvokeResult>;
}
