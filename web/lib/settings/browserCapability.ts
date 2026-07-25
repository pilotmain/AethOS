/** Browser automation capability — Mission Control Settings. */

export type BrowserDiagnostics = {
  python_executable?: string;
  python_version?: string;
  playwright_import_ok?: boolean;
  playwright_package?: string;
  playwright_version?: string | null;
  chromium_browser?: string;
  execution_ready?: boolean;
  install_hint?: string | null;
  recommended_install_commands?: string[];
  recommended_install_command?: string | null;
  import_error?: string | null;
  chromium_error?: string | null;
  browser_cache_path?: string | null;
  playwright_browsers_path_env?: string | null;
  chromium_executable_path?: string | null;
  launch_probe_ok?: boolean;
  launch_probe_error?: string | null;
  failure_kind?: string;
  failure_layer?: string;
  runtime_bug?: boolean;
  user_message?: string;
  install_command?: string | null;
  last_successful_browser_use_at?: number | null;
};

export type BrowserExecutorStatus = {
  running?: boolean;
  thread_id?: number | null;
  queue_depth?: number;
  launch_queue_depth?: number;
  active_operation?: string | null;
  last_error?: string | null;
  last_error_at?: number | null;
  last_success_at?: number | null;
};

export type BrowserCapabilityStatus = {
  enabled: boolean;
  available: boolean;
  provider: string;
  requires_approval: boolean;
  supports_login_sessions: boolean | string;
  active_session_count?: number;
  active_session?: { id: string; target: string; status: string } | null;
  status_label: string;
  foundation_label?: string;
  execution_label?: string;
  env_var?: string;
  playwright_installed?: boolean;
  playwright_package?: string;
  chromium_browser?: string;
  execution_ready?: boolean;
  execution_implemented?: boolean;
  failure_kind?: string;
  failure_layer?: string;
  runtime_bug?: boolean;
  user_message?: string;
  last_successful_browser_use_at?: number | null;
  diagnostics?: BrowserDiagnostics;
  saved_profile_count?: number;
  profile_store?: { profile_count?: number; profile_store_path?: string };
  executor_status?: BrowserExecutorStatus;
};

export type BrowserCapabilityViewModel = {
  foundationLabel: string;
  executionLabel: string;
  enabled: boolean;
  requiresApproval: boolean;
  loginSessionsLabel: string;
  activeSessionCount: number;
  envVar: string;
  userMessage: string;
  unavailable: boolean;
  runtimePython: string;
  playwrightPackage: string;
  chromiumBrowser: string;
  executionReady: boolean;
  installCommands: string[];
  recommendedInstallCommand: string;
  pythonVersion: string;
  playwrightVersion: string;
  browserCachePath: string;
  chromiumExecutablePath: string;
  launchProbeOk: boolean | null;
  launchProbeError: string | null;
  showDiagnostics: boolean;
  showInstallCommand: boolean;
  failureKind: string;
  runtimeBug: boolean;
  lastSuccessfulBrowserUseAt: number | null;
  savedProfileCount: number;
  profileStorePath: string;
  executorRunning: boolean;
  executorThreadId: string;
  executorQueueDepth: number;
  executorActiveOperation: string;
  executorLastError: string;
  executorLastSuccessAt: number | null;
};

export function normalizeBrowserCapability(input: unknown): BrowserCapabilityViewModel {
  const raw = input as Partial<BrowserCapabilityStatus> | null;
  if (!raw || typeof raw !== "object") {
    return emptyBrowserVm("Browser capability status is unavailable.", true);
  }
  const enabled = Boolean(raw.enabled);
  const diag = raw.diagnostics ?? {};
  const foundationLabel = String(
    raw.foundation_label ?? raw.status_label ?? (enabled ? "Ready" : "Off"),
  );
  const executionLabel = String(
    raw.execution_label ?? (enabled ? "Unknown" : "Not available (foundation off)"),
  );
  const envVar = String(raw.env_var ?? "BROWSER_AUTOMATION_ENABLED");
  const loginSessionsLabel =
    raw.supports_login_sessions === "supervised_only" || raw.supports_login_sessions === false
      ? "Supervised only"
      : String(raw.supports_login_sessions);
  const activeSessionCount = Number(raw.active_session_count ?? 0);
  const runtimePython = String(diag.python_executable ?? raw.diagnostics?.python_executable ?? "unknown");
  const playwrightPackage = String(raw.playwright_package ?? diag.playwright_package ?? "unknown");
  const chromiumBrowser = String(raw.chromium_browser ?? diag.chromium_browser ?? "unknown");
  const executionReady = Boolean(raw.execution_ready ?? diag.execution_ready);
  const failureKind = String(raw.failure_kind ?? diag.failure_kind ?? "unknown");
  const runtimeBug = Boolean(raw.runtime_bug ?? diag.runtime_bug);
  const lastSuccessfulBrowserUseAt =
    typeof raw.last_successful_browser_use_at === "number"
      ? raw.last_successful_browser_use_at
      : typeof diag.last_successful_browser_use_at === "number"
        ? diag.last_successful_browser_use_at
        : null;

  const executor = raw.executor_status ?? {};
  const savedProfileCount = Number(
    raw.saved_profile_count ?? raw.profile_store?.profile_count ?? 0,
  );
  const profileStorePath = String(raw.profile_store?.profile_store_path ?? "—");
  const executorRunning = Boolean(executor.running);
  const executorThreadId =
    typeof executor.thread_id === "number" ? String(executor.thread_id) : "—";
  const executorQueueDepth = Number(executor.queue_depth ?? 0);
  const executorActiveOperation = executor.active_operation
    ? String(executor.active_operation)
    : "—";
  const executorLastError = executor.last_error ? String(executor.last_error) : "—";
  const executorLastSuccessAt =
    typeof executor.last_success_at === "number" ? executor.last_success_at : null;

  const installCommands =
    diag.recommended_install_commands?.length
      ? [...diag.recommended_install_commands]
      : enabled && !executionReady
        ? [
            "python -m pip install playwright",
            "python -m playwright install chromium",
          ]
        : [];
  const recommendedInstallCommand = String(
    diag.recommended_install_command ?? diag.install_command ?? installCommands[0] ?? "",
  );

  const pythonVersion = String(diag.python_version ?? "");
  const playwrightVersion = String(diag.playwright_version ?? "—");
  const browserCachePath = String(diag.browser_cache_path ?? diag.playwright_browsers_path_env ?? "—");
  const chromiumExecutablePath = String(diag.chromium_executable_path ?? "—");
  const launchProbeOk =
    typeof diag.launch_probe_ok === "boolean" ? diag.launch_probe_ok : null;
  const launchProbeError = diag.launch_probe_error ? String(diag.launch_probe_error) : null;

  let userMessage = String(
    raw.user_message ??
      diag.user_message ??
      "Supervised browser sessions require approval. No credentials are stored.",
  );
  if (!enabled) {
    userMessage =
      "Browser automation is off. Set BROWSER_AUTOMATION_ENABLED=true in .env and restart the API.";
  } else if (executionReady) {
    userMessage =
      "Supervised sessions can open after approval. You log in manually; AethOS does not store credentials.";
    if (lastSuccessfulBrowserUseAt) {
      userMessage += " Browser runtime verified by a recent successful inspection.";
    }
  } else if (runtimeBug || failureKind === "sync_api_inside_asyncio_loop") {
    userMessage =
      "AethOS runtime bug: Playwright Sync API was called inside the asyncio event loop. Restart the API after updating. Do not run `playwright install` for this error.";
  } else if (playwrightPackage !== "installed") {
    userMessage =
      "Playwright package is missing in the AethOS runtime. Install using the commands below (same Python as the API).";
  } else if (chromiumBrowser === "missing") {
    userMessage =
      "Chromium is not installed for Playwright in this runtime. Run the Chromium install command below.";
  } else if (launchProbeOk === false) {
    userMessage = String(
      diag.user_message ??
        "Playwright is installed but Chromium could not be launched in this API process.",
    );
  }

  const showInstallCommand =
    !executionReady && !runtimeBug && Boolean(recommendedInstallCommand || installCommands.length);

  return {
    foundationLabel,
    executionLabel,
    enabled,
    requiresApproval: raw.requires_approval !== false,
    loginSessionsLabel,
    activeSessionCount,
    envVar,
    userMessage,
    unavailable: false,
    runtimePython,
    playwrightPackage,
    chromiumBrowser,
    executionReady,
    installCommands,
    recommendedInstallCommand,
    pythonVersion,
    playwrightVersion,
    browserCachePath,
    chromiumExecutablePath,
    launchProbeOk,
    launchProbeError,
    showDiagnostics: enabled || Boolean((raw as { browser_automation_enabled?: boolean }).browser_automation_enabled),
    showInstallCommand,
    failureKind,
    runtimeBug,
    lastSuccessfulBrowserUseAt,
    savedProfileCount,
    profileStorePath,
    executorRunning,
    executorThreadId,
    executorQueueDepth,
    executorActiveOperation,
    executorLastError,
    executorLastSuccessAt,
  };
}

function emptyBrowserVm(message: string, unavailable: boolean): BrowserCapabilityViewModel {
  return {
    foundationLabel: "Unknown",
    executionLabel: "Unknown",
    enabled: false,
    requiresApproval: true,
    loginSessionsLabel: "Supervised only",
    activeSessionCount: 0,
    envVar: "BROWSER_AUTOMATION_ENABLED",
    userMessage: message,
    unavailable,
    runtimePython: "unknown",
    playwrightPackage: "unknown",
    chromiumBrowser: "unknown",
    executionReady: false,
    installCommands: [],
    recommendedInstallCommand: "",
    pythonVersion: "",
    playwrightVersion: "—",
    browserCachePath: "—",
    chromiumExecutablePath: "—",
    launchProbeOk: null,
    launchProbeError: null,
    showDiagnostics: false,
    showInstallCommand: false,
    failureKind: "unknown",
    runtimeBug: false,
    lastSuccessfulBrowserUseAt: null,
    savedProfileCount: 0,
    profileStorePath: "—",
    executorRunning: false,
    executorThreadId: "—",
    executorQueueDepth: 0,
    executorActiveOperation: "—",
    executorLastError: "—",
    executorLastSuccessAt: null,
  };
}

export function primaryPlaywrightInstallCommand(vm: BrowserCapabilityViewModel): string {
  return vm.recommendedInstallCommand || vm.installCommands[vm.installCommands.length - 1] || "";
}

export function browserCardHeadline(_vm: BrowserCapabilityViewModel): string {
  return "Browser automation";
}

export function formatPackageLabel(value: string): string {
  if (value === "installed") return "Installed";
  if (value === "unknown") return "Unknown";
  return "Missing";
}

export function isBrowserActionType(actionType: string): boolean {
  return (
    actionType === "browser_status_check" ||
    actionType === "browser_navigation_plan" ||
    actionType === "browser_login_required_notice"
  );
}

export function browserActionDetail(action: {
  action_type: string;
  params?: Record<string, unknown>;
}): string | null {
  if (!isBrowserActionType(action.action_type)) return null;
  const target = String(action.params?.target ?? "unknown");
  const mode = String(action.params?.mode ?? "supervised");
  return `Target: ${target} · Mode: ${mode} · Approval required`;
}
