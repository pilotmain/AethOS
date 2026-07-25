"use client";

import { useCallback, useState } from "react";

import {
  browserCardHeadline,
  formatPackageLabel,
  primaryPlaywrightInstallCommand,
  type BrowserCapabilityViewModel,
} from "@/lib/settings/browserCapability";

type Props = {
  viewModel: BrowserCapabilityViewModel;
};

export function BrowserCapabilityCard({ viewModel: vm }: Props) {
  const [copyMsg, setCopyMsg] = useState("");
  const border = vm.unavailable
    ? "rgba(255,255,255,0.12)"
    : vm.enabled
      ? "rgba(34,211,238,0.25)"
      : "rgba(251,191,36,0.25)";
  const bg = vm.unavailable
    ? "rgba(255,255,255,0.03)"
    : vm.enabled
      ? "rgba(34,211,238,0.06)"
      : "rgba(251,191,36,0.06)";

  const installCmd = primaryPlaywrightInstallCommand(vm);

  const onCopyInstall = useCallback(async () => {
    if (!installCmd) return;
    try {
      await navigator.clipboard.writeText(installCmd);
      setCopyMsg("Install command copied.");
    } catch {
      setCopyMsg("Copy failed — select the command below.");
    }
    window.setTimeout(() => setCopyMsg(""), 3000);
  }, [installCmd]);

  return (
    <section
      style={{
        padding: 16,
        borderRadius: 14,
        border: `1px solid ${border}`,
        background: bg,
        marginBottom: 16,
      }}
    >
      <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>{browserCardHeadline(vm)}</h2>
      <dl style={{ margin: 0, fontSize: 13, lineHeight: 1.7 }}>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Browser automation foundation</dt>
        <dd style={{ margin: "0 0 8px", color: vm.enabled ? "var(--aethos-accent)" : "var(--aethos-warn)" }}>{vm.foundationLabel}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Execution engine</dt>
        <dd style={{ margin: "0 0 8px" }}>{vm.executionLabel}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Requires approval</dt>
        <dd style={{ margin: "0 0 8px" }}>{vm.requiresApproval ? "Yes" : "No"}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Login sessions</dt>
        <dd style={{ margin: "0 0 8px" }}>{vm.loginSessionsLabel}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Active sessions</dt>
        <dd style={{ margin: "0 0 8px" }}>{vm.activeSessionCount}</dd>
        <dt style={{ color: "var(--aethos-text-muted)" }}>Config flag</dt>
        <dd style={{ margin: "0 0 8px" }}>
          <code>{vm.envVar}</code>
        </dd>
      </dl>

      {vm.showDiagnostics && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            borderRadius: 10,
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <p style={{ margin: "0 0 8px", fontSize: 12, fontWeight: 600, color: "var(--aethos-text)" }}>
            Runtime diagnostics (AethOS API process)
          </p>
          <dl style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Runtime Python</dt>
            <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>
              <code>{vm.runtimePython}</code>
              {vm.pythonVersion ? ` (${vm.pythonVersion})` : null}
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Playwright package</dt>
            <dd style={{ margin: "0 0 6px" }}>
              {formatPackageLabel(vm.playwrightPackage)}
              {vm.playwrightVersion !== "—" ? ` · ${vm.playwrightVersion}` : null}
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Chromium browser</dt>
            <dd style={{ margin: "0 0 6px" }}>{formatPackageLabel(vm.chromiumBrowser)}</dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Browser cache path</dt>
            <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>
              <code>{vm.browserCachePath}</code>
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Chromium executable</dt>
            <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>
              <code>{vm.chromiumExecutablePath}</code>
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Launch probe</dt>
            <dd style={{ margin: "0 0 6px" }}>
              {vm.launchProbeOk === null
                ? "Not run"
                : vm.launchProbeOk
                  ? "OK — Chromium launched in this runtime"
                  : "Failed"}
              {vm.launchProbeError ? (
                <span style={{ display: "block", color: "var(--aethos-warn)", marginTop: 4 }}>{vm.launchProbeError}</span>
              ) : null}
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Execution ready</dt>
            <dd style={{ margin: "0 0 6px" }}>{vm.executionReady ? "Yes" : "No"}</dd>
            {vm.lastSuccessfulBrowserUseAt ? (
              <>
                <dt style={{ color: "var(--aethos-text-muted)" }}>Last successful browser use</dt>
                <dd style={{ margin: "0 0 6px" }}>
                  {new Date(vm.lastSuccessfulBrowserUseAt * 1000).toLocaleString()}
                </dd>
              </>
            ) : null}
            {vm.failureKind !== "ready" && vm.failureKind !== "unknown" ? (
              <>
                <dt style={{ color: "var(--aethos-text-muted)" }}>Failure kind</dt>
                <dd style={{ margin: "0 0 6px" }}>
                  <code>{vm.failureKind}</code>
                  {vm.runtimeBug ? " (AethOS runtime — not Chromium install)" : null}
                </dd>
              </>
            ) : null}
          </dl>
          <p style={{ margin: "12px 0 8px", fontSize: 12, fontWeight: 600, color: "var(--aethos-text)" }}>
            Profile store diagnostics
          </p>
          <dl style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Saved profile count</dt>
            <dd style={{ margin: "0 0 6px" }}>{vm.savedProfileCount}</dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Profile store path</dt>
            <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>
              <code>{vm.profileStorePath}</code>
            </dd>
          </dl>
          <p style={{ margin: "12px 0 8px", fontSize: 12, fontWeight: 600, color: "var(--aethos-text)" }}>
            Browser executor status
          </p>
          <dl style={{ margin: 0, fontSize: 12, lineHeight: 1.6 }}>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Executor running</dt>
            <dd style={{ margin: "0 0 6px" }}>{vm.executorRunning ? "Yes" : "No"}</dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Executor thread id</dt>
            <dd style={{ margin: "0 0 6px" }}>
              <code>{vm.executorThreadId}</code>
            </dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Queue depth</dt>
            <dd style={{ margin: "0 0 6px" }}>{vm.executorQueueDepth}</dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Active operation</dt>
            <dd style={{ margin: "0 0 6px" }}>{vm.executorActiveOperation}</dd>
            <dt style={{ color: "var(--aethos-text-muted)" }}>Last runtime error</dt>
            <dd style={{ margin: "0 0 6px", color: vm.executorLastError !== "—" ? "var(--aethos-warn)" : undefined }}>
              {vm.executorLastError}
            </dd>
            {vm.executorLastSuccessAt ? (
              <>
                <dt style={{ color: "var(--aethos-text-muted)" }}>Last successful browser operation</dt>
                <dd style={{ margin: "0 0 6px" }}>
                  {new Date(vm.executorLastSuccessAt * 1000).toLocaleString()}
                </dd>
              </>
            ) : null}
          </dl>
          {!vm.executionReady && vm.showInstallCommand && installCmd && (
            <div style={{ marginTop: 8 }}>
              <p style={{ margin: "0 0 4px", fontSize: 11, color: "var(--aethos-text-muted)" }}>Recommended install command:</p>
              <pre
                style={{
                  margin: "0 0 8px",
                  fontSize: 11,
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                  color: "var(--aethos-text)",
                }}
              >
                {installCmd}
              </pre>
              <button
                type="button"
                onClick={() => void onCopyInstall()}
                style={{
                  borderRadius: 8,
                  padding: "6px 12px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "1px solid rgba(96,165,250,0.35)",
                  background: "rgba(59,130,246,0.1)",
                  color: "var(--aethos-accent)",
                }}
              >
                Copy install command
              </button>
              {copyMsg ? (
                <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--aethos-ok)" }} role="status">
                  {copyMsg}
                </p>
              ) : null}
              <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--aethos-text-muted)" }}>Full setup:</p>
              <pre
                style={{
                  margin: 0,
                  fontSize: 11,
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                  color: "var(--aethos-text)",
                }}
              >
                {vm.installCommands.join("\n")}
              </pre>
            </div>
          )}
        </div>
      )}

      <p style={{ margin: "12px 0 0", fontSize: 13, lineHeight: 1.6 }}>{vm.userMessage}</p>
    </section>
  );
}
