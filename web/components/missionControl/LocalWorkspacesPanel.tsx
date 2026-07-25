"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  discoverPortfolioProjects,
  fetchPortfolio,
  fetchWorkspaceArchitecture,
  fetchWorkspaceDependencies,
  fetchWorkspaceStatus,
  fetchWorkspaceTests,
  registerGithubWorkspace,
  registerWorkspace,
  setPortfolioRoot,
  validateWorkspaceRegistrationPath,
  type PortfolioConfig,
  type PortfolioProject,
  type WorkspaceArtifact,
  type WorkspaceRecord,
  type EngineeringMemory,
} from "@/lib/missionControl/localWorkspaceApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  view: MissionControlView;
  hosted?: boolean;
  workspaces: WorkspaceRecord[];
  artifacts: WorkspaceArtifact[];
  engineeringMemory: EngineeringMemory;
  onRefresh: () => void;
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function StackBadges({ stack }: { stack?: WorkspaceRecord["stack"] }) {
  const badges = stack?.badges ?? [];
  if (badges.length === 0) return <span style={{ color: mcColors.textDim, fontSize: 12 }}>—</span>;
  return (
    <span style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {badges.map((b) => (
        <span
          key={b}
          style={{
            fontSize: 11,
            padding: "2px 8px",
            borderRadius: 999,
            background: "rgba(59,130,246,0.15)",
            color: "var(--aethos-accent)",
            border: "1px solid rgba(59,130,246,0.25)",
          }}
        >
          {b}
        </span>
      ))}
    </span>
  );
}

function WorkspaceCard({
  ws,
  onAnalyze,
  busy,
}: {
  ws: WorkspaceRecord;
  onAnalyze: (id: string, kind: "status" | "architecture" | "dependencies" | "tests") => void;
  busy: boolean;
}) {
  return (
    <article
      style={{
        padding: 14,
        borderRadius: 12,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.22)",
        marginBottom: 10,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>{ws.name}</div>
          <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>{ws.path}</div>
          {ws.remote_origin ? (
            <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>{ws.remote_origin}</div>
          ) : null}
        </div>
        <div style={{ textAlign: "right", fontSize: 12, color: mcColors.textMuted }}>
          <div>Branch: {ws.default_branch ?? "—"}</div>
          <div>Health: {ws.health_state ?? "—"}</div>
          <div>Scanned: {formatTs(ws.last_scan_at)}</div>
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <StackBadges stack={ws.stack} />
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
        {(["status", "architecture", "dependencies", "tests"] as const).map((kind) => (
          <button
            key={kind}
            type="button"
            disabled={busy}
            onClick={() => onAnalyze(ws.workspace_id, kind)}
            style={{ ...mcButtonSecondaryStyle, fontSize: 11, padding: "4px 10px" }}
          >
            {kind}
          </button>
        ))}
      </div>
    </article>
  );
}

export function LocalWorkspacesPanel({ view, hosted = false, workspaces, artifacts, engineeringMemory, onRefresh }: Props) {
  const [registerPath, setRegisterPath] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [githubBranch, setGithubBranch] = useState("");
  const [registerBusy, setRegisterBusy] = useState(false);
  const [registerError, setRegisterError] = useState("");
  const [analyzeBusy, setAnalyzeBusy] = useState(false);
  const [report, setReport] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [portfolioRoot, setPortfolioRootInput] = useState("");
  const [portfolio, setPortfolio] = useState<PortfolioConfig | null>(null);
  const [portfolioBusy, setPortfolioBusy] = useState(false);
  const [portfolioError, setPortfolioError] = useState("");
  const [discoveredProjects, setDiscoveredProjects] = useState<PortfolioProject[]>([]);

  const title = useMemo(() => {
    const labels: Partial<Record<MissionControlView, string>> = {
      "local-workspaces": hosted ? "Repositories" : "Local Workspaces",
      "repo-diagnostics": "Repo Diagnostics",
      "architecture-maps": "Architecture Maps",
      "git-activity": "Git Activity",
      "dependency-health": "Dependency Health",
      "test-intelligence": "Test Intelligence",
      "pr-proposals": "PR Proposals",
    };
    return labels[view] ?? "Engineering";
  }, [view, hosted]);

  const filteredArtifacts = useMemo(() => {
    if (view === "git-activity") {
      return artifacts.filter((a) => a.artifact_type === "git_status_snapshot");
    }
    if (view === "architecture-maps") {
      return artifacts.filter((a) => a.artifact_type === "architecture_analysis" || a.artifact_type === "local_repo_scan");
    }
    if (view === "dependency-health") {
      return artifacts.filter((a) => a.artifact_type === "dependency_audit");
    }
    if (view === "test-intelligence") {
      return artifacts.filter((a) => a.artifact_type === "test_failure_report" || a.artifact_type === "local_repo_scan");
    }
    if (view === "repo-diagnostics") {
      return artifacts.filter((a) =>
        ["local_repo_scan", "git_status_snapshot", "dependency_audit"].includes(a.artifact_type),
      );
    }
    return artifacts;
  }, [artifacts, view]);

  const registerWarning = useMemo(
    () => validateWorkspaceRegistrationPath(registerPath),
    [registerPath],
  );

  useEffect(() => {
    if (view !== "local-workspaces") return;
    if (portfolio?.portfolio_root) {
      setPortfolioRootInput(portfolio.portfolio_root);
      setDiscoveredProjects(portfolio.discovered ?? []);
    }
  }, [portfolio, view]);

  const handleSavePortfolioRoot = useCallback(async () => {
    const path = portfolioRoot.trim();
    if (!path) return;
    setPortfolioBusy(true);
    setPortfolioError("");
    try {
      const result = await setPortfolioRoot(path);
      setPortfolio(result.portfolio);
      setDiscoveredProjects(result.portfolio.discovered ?? []);
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : "Could not save portfolio root.");
    } finally {
      setPortfolioBusy(false);
    }
  }, [portfolioRoot]);

  const handleDiscoverProjects = useCallback(async (autoRegister: boolean) => {
    setPortfolioBusy(true);
    setPortfolioError("");
    try {
      const result = await discoverPortfolioProjects(autoRegister);
      setDiscoveredProjects(result.projects ?? []);
      onRefresh();
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : "Discovery failed.");
    } finally {
      setPortfolioBusy(false);
    }
  }, [onRefresh]);

  const handleRegisterProject = useCallback(async (path: string) => {
    setRegisterBusy(true);
    setRegisterError("");
    try {
      await registerWorkspace(path);
      onRefresh();
    } catch (err) {
      setRegisterError(err instanceof Error ? err.message : "Could not register project.");
    } finally {
      setRegisterBusy(false);
    }
  }, [onRefresh]);

  const handleRegisterGithub = useCallback(async () => {
    const repo = githubRepo.trim();
    if (!repo) return;
    setRegisterBusy(true);
    setRegisterError("");
    try {
      await registerGithubWorkspace(repo, githubBranch.trim());
      setGithubRepo("");
      setGithubBranch("");
      onRefresh();
    } catch (err) {
      setRegisterError(err instanceof Error ? err.message : "Could not connect GitHub repository.");
    } finally {
      setRegisterBusy(false);
    }
  }, [githubBranch, githubRepo, onRefresh]);

  const handleRegister = useCallback(async () => {
    const path = registerPath.trim();
    if (!path) return;
    const warning = validateWorkspaceRegistrationPath(path);
    if (warning) {
      setRegisterError(warning);
      return;
    }
    setRegisterBusy(true);
    setRegisterError("");
    try {
      await registerWorkspace(path);
      setRegisterPath("");
      onRefresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not register workspace.";
      setRegisterError(message);
    } finally {
      setRegisterBusy(false);
    }
  }, [registerPath, onRefresh]);

  const handleAnalyze = useCallback(async (workspaceId: string, kind: "status" | "architecture" | "dependencies" | "tests") => {
    setAnalyzeBusy(true);
    try {
      let result: { report?: string; tests?: Record<string, unknown> } = {};
      if (kind === "status") {
        result = await fetchWorkspaceStatus(workspaceId);
        setReportTitle("Git status (readonly)");
        setReport(result.report ?? "");
      } else if (kind === "architecture") {
        result = await fetchWorkspaceArchitecture(workspaceId);
        setReportTitle("Architecture map");
        setReport(result.report ?? "");
      } else if (kind === "dependencies") {
        result = await fetchWorkspaceDependencies(workspaceId);
        setReportTitle("Dependency audit");
        setReport(result.report ?? "");
      } else {
        const tests = await fetchWorkspaceTests(workspaceId);
        setReportTitle("Test intelligence");
        setReport(JSON.stringify(tests.tests ?? {}, null, 2));
      }
      onRefresh();
    } finally {
      setAnalyzeBusy(false);
    }
  }, [onRefresh]);

  useEffect(() => {
    if (view !== "local-workspaces") return;
    void fetchPortfolio()
      .then((data) => {
        setPortfolio(data.portfolio);
        if (data.portfolio.portfolio_root) {
          setPortfolioRootInput(data.portfolio.portfolio_root);
        }
        setDiscoveredProjects(data.portfolio.discovered ?? []);
      })
      .catch(() => {});
  }, [view, workspaces]);

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed local workspace intelligence — readonly analysis, auditable artifacts, no unrestricted shell.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {view === "local-workspaces" && (
        <div
          style={{
            marginTop: 16,
            padding: 14,
            borderRadius: 12,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(59,130,246,0.06)",
          }}
        >
          <h3 style={{ margin: "0 0 6px", fontSize: 14, fontWeight: 600 }}>Main workspace portfolio</h3>
          <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted, lineHeight: 1.5 }}>
            Set your projects folder (e.g. <code>~/projects</code>). AethOS discovers git repos underneath and resolves
            chat like a human: say a project name, or paste a path — &quot;look in ~/projects/my-app&quot;.
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input
              type="text"
              value={portfolioRoot}
              onChange={(e) => {
                setPortfolioRootInput(e.target.value);
                setPortfolioError("");
              }}
              placeholder="~/projects"
              style={{
                flex: "1 1 280px",
                padding: "8px 12px",
                borderRadius: 10,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.25)",
                color: mcColors.text,
                fontSize: 13,
              }}
            />
            <button type="button" disabled={portfolioBusy} onClick={() => void handleSavePortfolioRoot()} style={mcButtonSecondaryStyle}>
              Save portfolio root
            </button>
            <button type="button" disabled={portfolioBusy} onClick={() => void handleDiscoverProjects(false)} style={mcButtonSecondaryStyle}>
              Discover repos
            </button>
            <button type="button" disabled={portfolioBusy} onClick={() => void handleDiscoverProjects(true)} style={mcButtonSecondaryStyle}>
              Discover + register all
            </button>
          </div>
          {portfolioError ? (
            <div style={{ marginTop: 10, fontSize: 12, color: "var(--aethos-warn)" }}>{portfolioError}</div>
          ) : null}
          {discoveredProjects.length > 0 ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 12, color: mcColors.textMuted, marginBottom: 8 }}>
                {discoveredProjects.length} project{discoveredProjects.length === 1 ? "" : "s"} discovered
                {portfolio?.last_discovered_at ? ` · last scan ${formatTs(portfolio.last_discovered_at)}` : ""}
              </div>
              <div style={{ display: "grid", gap: 8, maxHeight: 280, overflow: "auto" }}>
                {discoveredProjects.map((project) => {
                  const registered = workspaces.some((ws) => ws.path === project.path);
                  return (
                    <div
                      key={project.path}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 10,
                        alignItems: "center",
                        padding: "8px 10px",
                        borderRadius: 10,
                        border: `1px solid ${mcColors.borderSubtle}`,
                        background: "rgba(0,0,0,0.18)",
                      }}
                    >
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 600 }}>{project.name}</div>
                        <div style={{ fontSize: 11, color: mcColors.textDim, overflow: "hidden", textOverflow: "ellipsis" }}>
                          {project.path}
                        </div>
                      </div>
                      <button
                        type="button"
                        disabled={registerBusy || registered}
                        onClick={() => void handleRegisterProject(project.path)}
                        style={{ ...mcButtonSecondaryStyle, fontSize: 11, padding: "4px 10px", flexShrink: 0 }}
                      >
                        {registered ? "Registered" : "Register"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {view === "local-workspaces" && hosted ? (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 10,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(59,130,246,0.08)",
            fontSize: 13,
            color: mcColors.textMuted,
          }}
        >
          This hosted deployment cannot read files on your laptop. Connect a <strong>GitHub repository</strong>{" "}
          (requires a GitHub token in Connections) and AethOS will analyze it server-side.
        </div>
      ) : null}

      {view === "local-workspaces" && hosted ? (
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            type="text"
            value={githubRepo}
            onChange={(e) => {
              setGithubRepo(e.target.value);
              setRegisterError("");
            }}
            placeholder="owner/repo (e.g. pilotmain/AethOS)"
            style={{
              flex: "1 1 220px",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.25)",
              color: mcColors.text,
              fontSize: 13,
            }}
          />
          <input
            type="text"
            value={githubBranch}
            onChange={(e) => setGithubBranch(e.target.value)}
            placeholder="branch (optional)"
            style={{
              flex: "0 1 140px",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.25)",
              color: mcColors.text,
              fontSize: 13,
            }}
          />
          <button
            type="button"
            disabled={registerBusy || !githubRepo.trim()}
            onClick={() => void handleRegisterGithub()}
            style={mcButtonSecondaryStyle}
          >
            Connect GitHub repo
          </button>
        </div>
      ) : null}

      {view === "local-workspaces" && !hosted && (
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            type="text"
            value={registerPath}
            onChange={(e) => {
              setRegisterPath(e.target.value);
              setRegisterError("");
            }}
            placeholder="/absolute/path/to/repo"
            style={{
              flex: "1 1 280px",
              padding: "8px 12px",
              borderRadius: 10,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.25)",
              color: mcColors.text,
              fontSize: 13,
            }}
          />
          <button
            type="button"
            disabled={registerBusy || Boolean(registerWarning)}
            onClick={() => void handleRegister()}
            style={mcButtonSecondaryStyle}
          >
            Register workspace
          </button>
        </div>
      )}

      {view === "local-workspaces" && (registerWarning || registerError) ? (
        <div
          style={{
            marginTop: 10,
            padding: 12,
            borderRadius: 10,
            border: "1px solid rgba(251,191,36,0.25)",
            background: "rgba(251,191,36,0.08)",
            fontSize: 13,
            color: "var(--aethos-warn)",
          }}
        >
          {registerError || registerWarning}
        </div>
      ) : null}

      {view === "pr-proposals" && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 10,
            border: "1px solid rgba(251,191,36,0.25)",
            background: "rgba(251,191,36,0.08)",
            fontSize: 13,
            color: "var(--aethos-warn)",
          }}
        >
          PR proposals are preflight-only. Changes require{" "}
          <code style={{ fontSize: 12 }}>code_mutation_preflight → approval → execution → verification → audit</code>.
          No auto-merge or unrestricted writes.
        </div>
      )}

      {(view === "local-workspaces" || view === "repo-diagnostics") && (
        <div style={{ marginTop: 16 }}>
          {workspaces.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              {hosted
                ? "No repositories connected. Add owner/repo above (GitHub token required in Connections)."
                : "No workspaces registered. Register a repo path or use chat: register local repo /path/to/repo"}
            </p>
          ) : (
            workspaces.map((ws) => (
              <WorkspaceCard key={ws.workspace_id} ws={ws} onAnalyze={handleAnalyze} busy={analyzeBusy} />
            ))
          )}
        </div>
      )}

      {report ? (
        <details open style={{ marginTop: 16 }}>
          <summary style={{ cursor: "pointer", fontSize: 13, color: mcColors.textMuted }}>{reportTitle}</summary>
          <pre
            style={{
              marginTop: 8,
              padding: 12,
              borderRadius: 12,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              fontSize: 12,
              lineHeight: 1.5,
              overflow: "auto",
              whiteSpace: "pre-wrap",
            }}
          >
            {report}
          </pre>
        </details>
      ) : null}

      <div style={{ marginTop: 20 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Evidence artifacts</h3>
        {filteredArtifacts.length === 0 ? (
          <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No artifacts yet — run a scan from chat or analyze a workspace.</p>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
            {filteredArtifacts.slice(0, 30).map((art) => (
              <li
                key={art.artifact_id}
                style={{
                  padding: "10px 12px",
                  marginBottom: 8,
                  borderRadius: 10,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  background: "rgba(0,0,0,0.18)",
                }}
              >
                <div style={{ color: mcColors.text }}>
                  {art.artifact_type} · {art.summary || art.artifact_id}
                </div>
                <div style={{ color: mcColors.textDim, fontSize: 12, marginTop: 4 }}>
                  {art.repo_path ?? "—"} · {formatTs(art.created_at)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {engineeringMemory.events && engineeringMemory.events.length > 0 && view === "local-workspaces" && (
        <div style={{ marginTop: 20 }}>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Engineering memory</h3>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
            {engineeringMemory.events.slice(0, 15).map((ev, i) => (
              <li key={`${ev.at}-${i}`} style={{ marginBottom: 6, color: mcColors.textMuted }}>
                {ev.event} · {ev.detail || "—"} · {formatTs(ev.at)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
