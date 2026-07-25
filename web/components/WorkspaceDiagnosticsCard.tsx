"use client";

type WorkspaceInfo = {
  workspace_root?: string;
  repo_root?: string;
  runtime_python?: string;
  profile_store_path?: string;
  build_commit?: string | null;
  api_process_started_at?: number | null;
  workspace_warning?: string | null;
  canonical_workspace_ok?: boolean;
};

type BuildInfo = {
  commit?: string | null;
  api_process_started_at?: number | null;
  web_build_timestamp?: string | null;
};

type Props = {
  workspace?: WorkspaceInfo | null;
  build?: BuildInfo | null;
};

function formatTs(ts: number | null | undefined): string {
  if (typeof ts !== "number") return "—";
  return new Date(ts * 1000).toISOString().replace("T", " ").slice(0, 19) + " UTC";
}

export function WorkspaceDiagnosticsCard({ workspace, build }: Props) {
  const ws = workspace ?? {};
  const b = build ?? {};
  const warning = ws.workspace_warning;

  return (
    <section
      style={{
        padding: 16,
        borderRadius: 14,
        border: warning
          ? "1px solid rgba(251,191,36,0.35)"
          : "1px solid rgba(255,255,255,0.1)",
        background: warning ? "rgba(251,191,36,0.06)" : "rgba(255,255,255,0.03)",
        marginBottom: 16,
      }}
    >
      <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>Workspace & build</h2>
      {warning ? (
        <p style={{ margin: "0 0 12px", fontSize: 13, color: "var(--aethos-warn)" }}>{warning}</p>
      ) : null}
      <dl style={{ margin: 0, fontSize: 13, lineHeight: 1.7 }}>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Workspace root</dt>
        <dd style={{ margin: "0 0 8px" }}>
          <code>{ws.workspace_root ?? "unknown"}</code>
        </dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Runtime Python</dt>
        <dd style={{ margin: "0 0 8px" }}>
          <code>{ws.runtime_python ?? "unknown"}</code>
        </dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Profile store</dt>
        <dd style={{ margin: "0 0 8px" }}>
          <code>{ws.profile_store_path ?? "unknown"}</code>
        </dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Build commit</dt>
        <dd style={{ margin: "0 0 8px" }}>
          <code>{b.commit ?? ws.build_commit ?? "unknown"}</code>
        </dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>API process start</dt>
        <dd style={{ margin: "0 0 8px" }}>{formatTs(b.api_process_started_at ?? ws.api_process_started_at)}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Web build</dt>
        <dd style={{ margin: 0 }}>{b.web_build_timestamp ?? "dev (no stamp)"}</dd>
      </dl>
    </section>
  );
}
