"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

import { ChatComposer } from "@/components/chat/ChatComposer";
import { ChatContextPanel } from "@/components/chat/ChatContextPanel";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatTimeline } from "@/components/chat/ChatTimeline";
import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import { fetchChat, fetchHealth, streamChat, StreamingUnavailableError } from "@/lib/api";
import { focusChatInput, isChatHomeRoute } from "@/lib/chat/focus";
import {
  isNearBottom,
  readPinnedToBottom,
  shouldShowJumpToLatest,
  writePinnedToBottom,
} from "@/lib/chat/autoScroll";
import {
  chatAppShellStyle,
  chatConversationColumnStyle,
  chatMainColumnStyle,
  chatWorkspaceGridStyle,
  isSidebarToggleShortcut,
} from "@/lib/chat/layout";
import { canSendChat, deriveChatHealth, type ChatHealth } from "@/lib/connection/chatHealth";
import {
  fetchActionEvents,
  getOrCreateChatSessionId,
  mergeLifecycleEvents,
  pruneSeenToDisplayed,
  readSeenEventIds,
  readTrackedActionIds,
  registerProposedActionFromMeta,
  writeSeenEventIds,
} from "@/lib/chat/actionLifecycleBridge";
import {
  detachTerminalJobFromThreads,
  fetchJobEvents,
  mergeJobLifecycleEvents,
  pruneSeenJobToDisplayed,
  readSeenJobEventIds,
  readTrackedJobIds,
  registerProposedJobFromMeta,
  trackJobId,
  writeSeenJobEventIds,
} from "@/lib/chat/jobLifecycleBridge";
import { cancelTrackedJob } from "@/lib/missionControl/trackedJobs";
import {
  liveUpdatesDelayedMessage,
  recordPollOutcome,
} from "@/lib/chat/jobEventPolling";
import {
  fetchBrowserSessionEvents,
  mergeBrowserLifecycleEvents,
  pruneSeenBrowserToDisplayed,
  readSeenBrowserEventIds,
  readTrackedBrowserSessionIds,
  registerBrowserSessionFromMeta,
  trackBrowserSessionFromActionEvent,
  writeSeenBrowserEventIds,
} from "@/lib/chat/browserLifecycleBridge";
import {
  formatChatError,
  readCachedMessages,
} from "@/lib/chat/lanes";
import type { CachedMessage } from "@/lib/chat/types";
import type { ChatInteractionMode, QueuedInput, QueuedInputKind } from "@/components/chat/ChatComposer";
import { PwaInstallBanner } from "@/components/pwa/PwaInstallBanner";
import { useVoice, type TranscriptHandler, type VoiceController } from "@/lib/voice/useVoice";
import {
  fetchModelCatalog,
  fetchSessionUsage,
  persistSessionModelOverride,
  readSessionModelOverride,
  type ModelCatalogEntry,
  type ModelCatalogSnapshot,
  type SessionUsage,
} from "@/lib/chat/modelSelection";
import {
  buildSessionExportHtml,
  buildSessionSummaryText,
  cloneActiveThread,
  createChatThread,
  deleteChatThread,
  exportFilename,
  addThreadJob,
  allActiveThreadJobIds,
  forkActiveThreadAtIndex,
  getActiveThread,
  getThreadMessages,
  listChatThreads,
  mergeServerThreadsIntoLocal,
  removeThreadJob,
  selectChatThread,
  sessionTreeOutline,
  threadsWithActiveJobs,
  titleFromMessages,
  updateThreadMessages,
  type ChatThread,
} from "@/lib/chat/chatThreads";
import {
  createServerThread,
  deleteServerThread,
  fetchServerThread,
  fetchServerThreadList,
  upsertServerThread,
} from "@/lib/chat/chatThreadsApi";

function id() {
  return `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return `${Math.round(n)}`;
}

/** Always-visible, honest usage strip: model · tokens this session · est. cost. */
function UsageStrip({
  usage,
  fallbackModel,
  turnMeta,
}: {
  usage: SessionUsage | null;
  fallbackModel: string | null;
  turnMeta: Record<string, string> | null;
}) {
  const sess = usage?.session ?? null;
  // Transparency: when the agent tool loop swapped to a cloud model, show the
  // selected model AND the model that actually answered — never a silent mismatch.
  const fellBack = turnMeta?.tool_fallback === "true";
  const selectedLabel = turnMeta?.selected_model_label || turnMeta?.selected_model || null;
  const actualModel = turnMeta?.effective_model || turnMeta?.tool_fallback_model || null;
  // §2 honest split — when a session ran on >1 model, show each model's share +
  // cost (local reads $0.00, never "n/a"): "Qwen2.5 14B 72% ($0.00) · opus 28% ($0.34)".
  const split = (sess?.models ?? []).filter((m) => m.pct > 0);
  const splitLabel =
    split.length > 1
      ? split.map((m) => `${m.model} ${m.pct}% (${m.cost.label})`).join(" · ")
      : null;
  const model = splitLabel
    ? splitLabel
    : fellBack && selectedLabel && actualModel
      ? `${selectedLabel} → tools ran on ${actualModel}`
      : sess?.model || usage?.model || fallbackModel || "—";
  const tokens = sess?.tokens.total ?? 0;
  const inTok = sess?.tokens.input ?? 0;
  const outTok = sess?.tokens.output ?? 0;
  const cost = sess?.cost ?? usage?.cost ?? { label: "—", known: false, usd: null };
  const ctx = sess?.context ?? usage?.context ?? null;
  const cache = sess?.cache ?? usage?.cache ?? null;
  // Show a calm em dash (not "n/a", which reads as broken) until a turn reports
  // real numbers; the model still resolves so the strip never looks empty.
  const ctxLabel =
    ctx && ctx.known && ctx.used != null && ctx.limit != null
      ? `${formatTokens(ctx.used)}/${formatTokens(ctx.limit)} (${ctx.pct}%)`
      : "—";
  const cacheLabel = cache && cache.known && cache.hit_ratio != null ? `${cache.hit_ratio}%` : "—";
  return (
    <div
      data-aethos-usage-strip
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        flexWrap: "wrap",
        padding: "5px 16px",
        fontSize: 11.5,
        color: "var(--aethos-text-muted)",
        borderBottom: "1px solid var(--aethos-border)",
        background: "var(--aethos-surface)",
      }}
      title={`Input ${inTok} · output ${outTok} tokens this session`}
    >
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
        <span style={{ color: "var(--aethos-text-dim)" }}>Model</span>
        <strong
          style={{ color: fellBack ? "var(--aethos-warn)" : "var(--aethos-text)", fontWeight: 600 }}
          title={fellBack ? "Selected model can't run tools in agent mode; tools ran on the cloud fallback." : undefined}
        >
          {model}
        </strong>
      </span>
      <span style={{ color: "var(--aethos-border)" }}>·</span>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
        <span style={{ color: "var(--aethos-text-dim)" }}>Tokens</span>
        <strong style={{ color: "var(--aethos-text)", fontWeight: 600 }}>{formatTokens(tokens)}</strong>
        <span style={{ color: "var(--aethos-text-dim)" }}>this session</span>
      </span>
      <span style={{ color: "var(--aethos-border)" }}>·</span>
      <span
        style={{ display: "inline-flex", alignItems: "center", gap: 5 }}
        title="Most recent turn context window used"
      >
        <span style={{ color: "var(--aethos-text-dim)" }}>Ctx</span>
        <strong style={{ color: "var(--aethos-text)", fontWeight: 600 }}>{ctxLabel}</strong>
      </span>
      <span style={{ color: "var(--aethos-border)" }}>·</span>
      <span
        style={{ display: "inline-flex", alignItems: "center", gap: 5 }}
        title="Prompt-cache hit ratio this session"
      >
        <span style={{ color: "var(--aethos-text-dim)" }}>Cache</span>
        <strong
          style={{
            color: cache && cache.known ? "var(--aethos-accent)" : "var(--aethos-text-dim)",
            fontWeight: 600,
          }}
        >
          {cacheLabel}
        </strong>
      </span>
      <span style={{ color: "var(--aethos-border)" }}>·</span>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
        <span style={{ color: "var(--aethos-text-dim)" }}>Est. cost</span>
        <strong
          style={{
            color: cost.known ? "var(--aethos-ok)" : "var(--aethos-text-dim)",
            fontWeight: 600,
          }}
        >
          {cost.label}
        </strong>
      </span>
    </div>
  );
}

export function ChatShell() {
  const { scope } = useAuthScope();
  const [threads, setThreads] = useState<ChatThread[]>(() =>
    typeof window !== "undefined" ? listChatThreads() : [],
  );
  const [activeThreadId, setActiveThreadId] = useState(() =>
    typeof window !== "undefined" ? getActiveThread().id : "",
  );
  const [messages, setMessages] = useState<CachedMessage[]>(() => readCachedMessages());
  const [input, setInput] = useState("");
  // Concurrency: each thread can have its own in-flight turn. We track the set
  // of threads currently generating; `sending` is derived for the *visible*
  // thread (drives the composer/stop button), while unfocused busy threads show
  // a "working…" indicator in the sidebar.
  const [busyThreadIds, setBusyThreadIds] = useState<string[]>([]);
  const [interactionMode, setInteractionMode] = useState<ChatInteractionMode>(() => {
    if (typeof window === "undefined") return "agent";
    return (localStorage.getItem("aethos_chat_interaction_mode") as ChatInteractionMode) || "agent";
  });
  const [modelCatalogId, setModelCatalogId] = useState("default");
  const [modelOptions, setModelOptions] = useState<ModelCatalogEntry[]>([]);
  const [modelCatalogLoading, setModelCatalogLoading] = useState(false);
  const [effectiveModel, setEffectiveModel] = useState<ModelCatalogSnapshot["effective"] | null>(null);
  const [usage, setUsage] = useState<SessionUsage | null>(null);
  const [lastTurnMeta, setLastTurnMeta] = useState<Record<string, string> | null>(null);
  const [queued, setQueued] = useState<QueuedInput[]>([]);
  const [err, setErr] = useState("");
  const [health, setHealth] = useState<ChatHealth | null>(null);
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  // Desktop sidebar collapse (toggled by Ctrl/⌘+B), persisted across reloads.
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);
  const sessionId = useRef(getOrCreateChatSessionId());
  // Live mirror of the focused thread so a running turn can decide whether to
  // paint into the visible buffer without reading a stale closure value.
  const activeThreadIdRef = useRef(activeThreadId);
  activeThreadIdRef.current = activeThreadId;
  const markThreadBusy = useCallback((threadId: string) => {
    setBusyThreadIds((ids) => (ids.includes(threadId) ? ids : [...ids, threadId]));
  }, []);
  const clearThreadBusy = useCallback((threadId: string) => {
    setBusyThreadIds((ids) => ids.filter((x) => x !== threadId));
  }, []);
  // Threads with a durable agent job still running server-side. Independent of
  // `busyThreadIds` (a live stream): a job keeps a thread "working" even after
  // its HTTP turn returned, and across navigation / reload.
  const [jobBusyThreadIds, setJobBusyThreadIds] = useState<string[]>(() =>
    typeof window !== "undefined" ? threadsWithActiveJobs() : [],
  );
  const refreshJobBusy = useCallback(() => setJobBusyThreadIds(threadsWithActiveJobs()), []);
  // The focused thread is "sending" while it has either a live stream or a
  // durable agent job still running — both keep the composer in Stop mode so the
  // operator can cancel, while background threads stay independent.
  const sending =
    busyThreadIds.includes(activeThreadId) || jobBusyThreadIds.includes(activeThreadId);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  // Live mirror of the voice controller so the send pipeline can speak replies
  // without re-binding on every voice state change (the hook is created below).
  const voiceRef = useRef<VoiceController | null>(null);
  const awayFromBottomRef = useRef(false);
  const didMountScrollRef = useRef(false);
  const [liveUpdatesStatus, setLiveUpdatesStatus] = useState("");
  const jobPollFailuresRef = useRef(0);
  // §2 streaming — one abort controller per in-flight turn, keyed by the thread
  // that started it. Switching threads must never abort another thread's turn;
  // the stop button only aborts the focused thread's controller.
  const streamAbortsRef = useRef<Map<string, AbortController>>(new Map());
  const streamingDisabledRef = useRef(false);
  const pathname = usePathname() ?? "/";

  useEffect(() => {
    if (!isChatHomeRoute(pathname)) return;
    focusChatInput(inputRef.current);
  }, [pathname]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ block: "end", behavior });
  }, []);

  const syncScrollState = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const near = isNearBottom(el);
    awayFromBottomRef.current = !near;
    writePinnedToBottom(near);
    if (near) setShowJumpToLatest(false);
  }, []);

  const refreshHealth = useCallback(async () => {
    if (sending) return;
    try {
      const h = await fetchHealth();
      setHealth(deriveChatHealth(h));
    } catch {
      setHealth({ chatReady: false, connectionLabel: "API offline", panelState: "healthy" });
    }
  }, [sending]);

  useEffect(() => {
    void refreshHealth();
    const t = window.setInterval(() => {
      if (document.visibilityState === "visible") void refreshHealth();
    }, 30_000);
    return () => window.clearInterval(t);
  }, [refreshHealth]);

  // Reconnect to durable agent jobs after a reload / tab reopen: re-track any
  // job ids still attached to a thread so the lifecycle poller resumes and the
  // running indicator reflects work that kept going while the UI was gone.
  useEffect(() => {
    for (const jobId of allActiveThreadJobIds()) trackJobId(jobId);
    refreshJobBusy();
  }, [refreshJobBusy]);

  useEffect(() => {
    const active = getActiveThread();
    setThreads(listChatThreads());
    setActiveThreadId(active.id);
    sessionId.current = active.sessionId;
    setMessages(active.messages);

    void (async () => {
      const summaries = await fetchServerThreadList();
      if (summaries.length === 0) return;
      const details = await Promise.all(
        summaries.slice(0, 12).map(async (row) => {
          const thread = await fetchServerThread(row.session_id);
          return thread
            ? {
                session_id: thread.session_id,
                title: thread.title,
                created_at: thread.created_at,
                updated_at: thread.updated_at,
                messages: thread.messages,
              }
            : {
                session_id: row.session_id,
                title: row.title,
                created_at: row.created_at,
                updated_at: row.updated_at,
                messages: [],
              };
        }),
      );
      mergeServerThreadsIntoLocal(details);
      const nextActive = getActiveThread();
      setThreads(listChatThreads());
      setActiveThreadId(nextActive.id);
      sessionId.current = nextActive.sessionId;
      setMessages(nextActive.messages);
    })();
  }, [scope]);

  useEffect(() => {
    // §4 — upsert the *displayed* thread only (its own id/session), never the
    // shared global-active pointer that another window/tab may have flipped.
    if (!activeThreadId) return;
    const sid = sessionId.current;
    const title =
      listChatThreads().find((t) => t.id === activeThreadId)?.title || titleFromMessages(messages);
    const timer = window.setTimeout(() => {
      void upsertServerThread(sid, title, messages);
    }, 900);
    return () => window.clearTimeout(timer);
  }, [messages, activeThreadId]);

  useEffect(() => {
    // §4 — persist to the window's own thread id (thread-id-scoped), so a second
    // window/tab can never clobber this thread's messages via the shared pointer.
    if (!activeThreadId) return;
    updateThreadMessages(activeThreadId, messages);
  }, [messages, activeThreadId]);

  useEffect(() => {
    localStorage.setItem("aethos_chat_interaction_mode", interactionMode);
  }, [interactionMode]);

  const refreshModelCatalog = useCallback(async (sid: string) => {
    setModelCatalogLoading(true);
    try {
      const snapshot = await fetchModelCatalog(sid);
      setModelOptions(snapshot.models ?? []);
      const stored = readSessionModelOverride(sid);
      const nextId = stored || snapshot.session_override || snapshot.effective?.catalog_id || "default";
      setModelCatalogId(nextId);
      setEffectiveModel(snapshot.effective ?? null);
    } catch {
      setModelOptions([{ id: "default", provider: "template", model: "template", label: "Default (.env)", configured: false }]);
      setModelCatalogId("default");
      setEffectiveModel(null);
    } finally {
      setModelCatalogLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshModelCatalog(sessionId.current);
  }, [activeThreadId, refreshModelCatalog]);

  const refreshUsage = useCallback(async () => {
    const next = await fetchSessionUsage(sessionId.current);
    if (next) setUsage(next);
  }, []);

  useEffect(() => {
    void refreshUsage();
    const t = window.setInterval(() => {
      if (document.visibilityState === "visible") void refreshUsage();
    }, 10000);
    return () => window.clearInterval(t);
  }, [activeThreadId, refreshUsage]);

  const handleModelChange = useCallback(
    (catalogId: string) => {
      setModelCatalogId(catalogId);
      const sid = sessionId.current;
      void persistSessionModelOverride(sid, catalogId === "default" ? null : catalogId)
        .then((effective) => setEffectiveModel(effective))
        .catch(() => void refreshModelCatalog(sid));
    },
    [refreshModelCatalog],
  );

  // §9 fast model switch — Ctrl/Cmd+M cycles the configured models (+ default).
  const cycleModel = useCallback(() => {
    const ids = ["default", ...modelOptions.filter((m) => m.configured).map((m) => m.id)];
    if (ids.length < 2) return;
    const current = ids.indexOf(modelCatalogId);
    const next = ids[(current + 1) % ids.length];
    handleModelChange(next);
  }, [modelOptions, modelCatalogId, handleModelChange]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "m") {
        e.preventDefault();
        cycleModel();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cycleModel]);

  // (Ctrl/⌘+B is handled by a single listener lower down that toggles the desktop
  // collapse state and the mobile overlay correctly — the old mobile-only handler
  // that used to live here did nothing on desktop and fought the collapse state.)

  const switchThread = useCallback((threadId: string) => {
    const row = selectChatThread(threadId);
    if (!row) return;
    setActiveThreadId(row.id);
    sessionId.current = row.sessionId;
    setMessages(row.messages);
    setInput("");
    setErr("");
    setThreads(listChatThreads());
    void refreshModelCatalog(row.sessionId);
  }, [refreshModelCatalog]);

  const handleNewChat = useCallback(() => {
    const row = createChatThread();
    setActiveThreadId(row.id);
    sessionId.current = row.sessionId;
    setMessages([]);
    setInput("");
    setErr("");
    setThreads(listChatThreads());
    void createServerThread(row.sessionId, row.title);
    void refreshModelCatalog(row.sessionId);
    focusChatInput(inputRef.current);
  }, [refreshModelCatalog]);

  const handleDeleteThread = useCallback(
    (threadId: string) => {
      const current = threads.find((t) => t.id === threadId);
      // Deleting a thread is an explicit teardown — abort its turn if running.
      streamAbortsRef.current.get(threadId)?.abort();
      streamAbortsRef.current.delete(threadId);
      clearThreadBusy(threadId);
      const next = deleteChatThread(threadId);
      if (!next) return;
      if (current?.sessionId) void deleteServerThread(current.sessionId);
      setActiveThreadId(next.id);
      sessionId.current = next.sessionId;
      setMessages(next.messages);
      setThreads(listChatThreads());
      void refreshModelCatalog(next.sessionId);
    },
    [threads, refreshModelCatalog, clearThreadBusy],
  );

  const pollActionLifecycle = useCallback(async () => {
    const ids = readTrackedActionIds();
    if (ids.length === 0) return;
    const events = await fetchActionEvents(ids);
    if (events.length === 0) return;
    setMessages((prev) => {
      let seen = pruneSeenToDisplayed(prev, readSeenEventIds());
      const merged = mergeLifecycleEvents(prev, events, seen);
      for (const ev of events) {
        trackBrowserSessionFromActionEvent(ev);
      }
      if (merged.added > 0) {
        writeSeenEventIds(merged.seen);
        return merged.messages;
      }
      return prev;
    });
  }, []);

  const pollJobLifecycle = useCallback(async () => {
    const ids = readTrackedJobIds();
    if (ids.length === 0) {
      jobPollFailuresRef.current = 0;
      setLiveUpdatesStatus("");
      return;
    }
    const result = await fetchJobEvents(ids);
    const backoff = recordPollOutcome(jobPollFailuresRef.current, result.ok);
    jobPollFailuresRef.current = backoff.consecutiveFailures;
    if (result.ok) {
      setLiveUpdatesStatus("");
    } else if (backoff.showStatus) {
      setLiveUpdatesStatus(liveUpdatesDelayedMessage());
    }
    if (!result.ok || result.events.length === 0) return;
    // A terminal lifecycle event means the durable job finished — detach it from
    // its thread so the "working…" indicator clears (on this thread or any
    // background one).
    let clearedAny = false;
    for (const event of result.events) {
      if (
        event.event_type === "job_completed" ||
        event.event_type === "job_failed" ||
        event.event_type === "job_cancelled"
      ) {
        await detachTerminalJobFromThreads(event.job_id);
        clearedAny = true;
      }
    }
    if (clearedAny) {
      refreshJobBusy();
      setThreads(listChatThreads());
    }
    setMessages((prev) => {
      const seen = pruneSeenJobToDisplayed(prev, readSeenJobEventIds());
      const merged = mergeJobLifecycleEvents(prev, result.events, seen);
      if (merged.added > 0) {
        writeSeenJobEventIds(merged.seen);
        return merged.messages;
      }
      return prev;
    });
  }, [refreshJobBusy]);

  const pollBrowserLifecycle = useCallback(async () => {
    const ids = readTrackedBrowserSessionIds();
    if (ids.length === 0) return;
    const events = await fetchBrowserSessionEvents(ids);
    if (events.length === 0) return;
    setMessages((prev) => {
      const seen = pruneSeenBrowserToDisplayed(prev, readSeenBrowserEventIds());
      const merged = mergeBrowserLifecycleEvents(prev, events, seen);
      if (merged.added > 0) {
        writeSeenBrowserEventIds(merged.seen);
        return merged.messages;
      }
      return prev;
    });
  }, []);

  // §C2 — one consolidated lifecycle poller for action + job + browser events.
  // Replaces three independent 3s intervals. Pauses entirely when the tab is
  // hidden (visibilitychange) and backs off to 15s when nothing is being tracked,
  // snapping back to 3s on activity or when the tab returns to the foreground.
  useEffect(() => {
    const ACTIVE_MS = 3000;
    const IDLE_MS = 15000;
    let timer: number | null = null;
    let stopped = false;

    const hasTrackedWork = () =>
      readTrackedActionIds().length > 0 ||
      readTrackedJobIds().length > 0 ||
      readTrackedBrowserSessionIds().length > 0;

    const tick = async () => {
      if (stopped) return;
      if (document.visibilityState !== "visible") return; // paused while backgrounded
      await Promise.allSettled([
        pollActionLifecycle(),
        pollJobLifecycle(),
        pollBrowserLifecycle(),
      ]);
    };

    const schedule = () => {
      if (stopped) return;
      if (timer !== null) window.clearTimeout(timer);
      if (document.visibilityState !== "visible") return; // no timer while hidden
      const delay = hasTrackedWork() ? ACTIVE_MS : IDLE_MS;
      timer = window.setTimeout(async () => {
        await tick();
        schedule();
      }, delay);
    };

    const kick = () => {
      if (document.visibilityState === "visible") {
        void tick();
        schedule();
      }
    };

    // Initial run + scheduling.
    kick();

    const onVisible = () => {
      if (document.visibilityState === "visible") {
        kick(); // resume immediately with a fresh poll
      } else if (timer !== null) {
        window.clearTimeout(timer); // suspend while hidden
        timer = null;
      }
    };
    window.addEventListener("focus", kick);
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      stopped = true;
      if (timer !== null) window.clearTimeout(timer);
      window.removeEventListener("focus", kick);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [pollActionLifecycle, pollJobLifecycle, pollBrowserLifecycle]);

  useLayoutEffect(() => {
    if (!didMountScrollRef.current && messages.length > 0 && readPinnedToBottom()) {
      didMountScrollRef.current = true;
      scrollToBottom("auto");
      return;
    }
    didMountScrollRef.current = true;

    if (!awayFromBottomRef.current) {
      scrollToBottom(sending ? "auto" : "smooth");
      setShowJumpToLatest(false);
    } else {
      setShowJumpToLatest(
        shouldShowJumpToLatest(scrollContainerRef.current, true, messages.length > 0),
      );
    }
  }, [messages, sending, scrollToBottom]);

  const jumpToLatest = () => {
    awayFromBottomRef.current = false;
    writePinnedToBottom(true);
    setShowJumpToLatest(false);
    scrollToBottom("smooth");
  };

  const appendSystemNote = useCallback((note: string) => {
    setMessages((m) => [...m, { id: id(), role: "system", content: note }]);
    requestAnimationFrame(() => scrollToBottom("auto"));
  }, [scrollToBottom]);

  // §4 — switch React state onto a freshly created/forked thread.
  const activateThread = useCallback(
    (thread: ChatThread) => {
      setActiveThreadId(thread.id);
      sessionId.current = thread.sessionId;
      setMessages(thread.messages);
      setThreads(listChatThreads());
      setInput("");
      setErr("");
      void refreshModelCatalog(thread.sessionId);
      requestAnimationFrame(() => scrollToBottom("auto"));
    },
    [refreshModelCatalog, scrollToBottom],
  );

  // §6/§4 — local slash commands handled client-side (never sent to the model).
  // Returns true when the input was a recognized command.
  const runLocalCommand = useCallback(
    (raw: string): boolean => {
      const trimmed = raw.trim();
      const lower = trimmed.toLowerCase();
      const verb = lower.split(/\s+/)[0];
      const thread = getActiveThread();

      // §4 session tree — tree / fork / clone.
      if (verb === "/tree") {
        appendSystemNote(sessionTreeOutline(thread));
        return true;
      }
      if (verb === "/fork") {
        const n = parseInt(trimmed.split(/\s+/)[1] ?? "", 10);
        const target = Number.isFinite(n) ? n : thread.messages.length;
        const fork = forkActiveThreadAtIndex(target);
        if (!fork) {
          appendSystemNote(`Can't fork at ${target}. Use /tree to see valid message numbers.`);
          return true;
        }
        activateThread(fork);
        appendSystemNote(
          `Forked a new branch from message ${target}. The original thread is unchanged — switch back any time from the sidebar.`,
        );
        return true;
      }
      if (verb === "/clone") {
        const clone = cloneActiveThread();
        activateThread(clone);
        appendSystemNote("Cloned this branch into a new thread. The original is preserved in the sidebar.");
        return true;
      }

      if (lower !== "/export" && lower !== "/copy") return false;
      const cmd = lower;
      if (cmd === "/export") {
        try {
          const html = buildSessionExportHtml(thread);
          const blob = new Blob([html], { type: "text/html" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = exportFilename(thread);
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.setTimeout(() => URL.revokeObjectURL(url), 1000);
          appendSystemNote(`Exported ${thread.messages.length} messages → ${exportFilename(thread)} (saved locally).`);
        } catch {
          appendSystemNote("Export failed — your browser blocked the download.");
        }
        return true;
      }
      // /copy
      void navigator.clipboard
        ?.writeText(buildSessionSummaryText(thread))
        .then(() => appendSystemNote("Copied a shareable text summary of this session to your clipboard."))
        .catch(() => appendSystemNote("Copy failed — clipboard access was denied."));
      return true;
    },
    [appendSystemNote, activateThread],
  );

  const send = async (overrideText?: string, opts?: { surface?: string }) => {
    const fromQueue = overrideText != null;
    const turnSurface = opts?.surface || "webchat";
    const text = (overrideText ?? input).trim();
    if (!text || sending) return;
    if (text.startsWith("/") && runLocalCommand(text)) {
      if (!fromQueue) setInput("");
      return;
    }
    if (health && !canSendChat(health)) {
      setErr("Chat unavailable — check API connection.");
      return;
    }
    if (!fromQueue) setInput("");
    setErr("");

    // Capture the turn's identity BEFORE any await. The operator may switch
    // threads mid-stream; this turn must stay bound to the thread/session that
    // started it and never read the shared `sessionId.current` again.
    const turnThreadId = activeThreadId;
    const turnSessionId = sessionId.current;
    markThreadBusy(turnThreadId);

    awayFromBottomRef.current = false;
    writePinnedToBottom(true);
    setShowJumpToLatest(false);

    const userId = id();
    const asstId = id();
    const prior = getThreadMessages(turnThreadId);
    const userMsg: CachedMessage = {
      id: userId,
      role: "user",
      content: text,
      parentId: prior[prior.length - 1]?.id,
    };
    const asstMsg: CachedMessage = { id: asstId, role: "assistant", content: "", parentId: userId };
    // `turnMessages` is the turn's authoritative working copy of its thread, so
    // we can persist to the originating thread store even while it's unfocused.
    let turnMessages: CachedMessage[] = [...prior, userMsg, asstMsg];

    const isFocused = () => turnThreadId === activeThreadIdRef.current;

    // Apply a mutation to this turn's assistant message. When the originating
    // thread is the one on screen we paint into the visible React buffer (the
    // `writeCachedMessages` effect persists it); when it's in the background we
    // write straight to that thread's store so nothing is lost.
    const applyToAssistant = (mutate: (row: CachedMessage) => CachedMessage) => {
      turnMessages = turnMessages.map((row) => (row.id === asstId ? mutate(row) : row));
      if (isFocused()) {
        setMessages((m) => m.map((row) => (row.id === asstId ? mutate(row) : row)));
      } else {
        updateThreadMessages(turnThreadId, turnMessages);
      }
    };

    if (isFocused()) {
      setMessages((m) => [...m, userMsg, asstMsg]);
      requestAnimationFrame(() => scrollToBottom("auto"));
    } else {
      updateThreadMessages(turnThreadId, turnMessages);
    }
    setThreads(listChatThreads());

    const modelArg = interactionMode === "agent" ? modelCatalogId : null;
    try {
      let out;
      if (!streamingDisabledRef.current) {
        const controller = new AbortController();
        streamAbortsRef.current.set(turnThreadId, controller);
        try {
          out = await streamChat(text, turnSessionId, interactionMode, modelArg, {
            signal: controller.signal,
            surface: turnSurface,
            onDelta: (t) => applyToAssistant((row) => ({ ...row, content: (row.content || "") + t })),
            // §3 — live activity feed: merge each step by id (running -> done/failed)
            // and append thoughts, so the operator watches the work as it happens.
            onStep: (evt) =>
              applyToAssistant((row) => {
                const prior = row.progress ?? [];
                if (evt.type === "thought") {
                  return { ...row, progress: [...prior, evt] };
                }
                const idx = prior.findIndex((p) => p.type === "step" && p.id === evt.id);
                if (idx === -1) return { ...row, progress: [...prior, evt] };
                const merged = prior.slice();
                merged[idx] = { ...merged[idx], ...evt, action: evt.action ?? merged[idx].action };
                return { ...row, progress: merged };
              }),
          });
        } catch (streamErr) {
          if (streamErr instanceof StreamingUnavailableError) {
            streamingDisabledRef.current = true;
            out = await fetchChat(text, turnSessionId, interactionMode, modelArg, turnSurface);
          } else if (streamErr instanceof DOMException && streamErr.name === "AbortError") {
            // User stopped mid-stream — keep the partial text, end gracefully.
            applyToAssistant((row) => ({
              ...row,
              content: `${row.content || ""}\n\n_[stopped]_`.trim(),
            }));
            setThreads(listChatThreads());
            return;
          } else {
            throw streamErr;
          }
        } finally {
          streamAbortsRef.current.delete(turnThreadId);
        }
      } else {
        out = await fetchChat(text, turnSessionId, interactionMode, modelArg, turnSurface);
      }
      const reply = (out.reply || "").trim() || "No response body.";
      // §2/§4 — speak the governed reply when the turn arrived by voice (or the
      // operator toggled "speak replies"). Mutations are spoken back as preflight
      // summaries because this is the same governed reply shown on screen.
      if (isFocused()) {
        voiceRef.current?.speakReply(reply, { force: turnSurface === "voice" });
      }
      if (isFocused()) setLastTurnMeta((out.meta ?? null) as Record<string, string> | null);
      registerProposedActionFromMeta(
        { ...(out.meta ?? {}), action: out.action ?? undefined },
        reply,
      );
      const turnJobId = registerProposedJobFromMeta(
        { ...(out.meta ?? {}), job: out.job ?? undefined },
        reply,
      );
      const orchestrationJobId =
        out.meta && typeof out.meta.orchestration_job_id === "string"
          ? out.meta.orchestration_job_id
          : null;
      // A durable agent job belongs to the thread that launched it: persist it
      // so the run survives navigation / reload and the thread keeps a "working…"
      // indicator until the job reaches a terminal lifecycle event.
      if (turnJobId) {
        addThreadJob(turnThreadId, turnJobId);
        if (orchestrationJobId && orchestrationJobId !== turnJobId) {
          addThreadJob(turnThreadId, orchestrationJobId);
          removeThreadJob(turnJobId);
        }
        refreshJobBusy();
      }
      registerBrowserSessionFromMeta(out.meta ?? undefined);
      applyToAssistant((row) => ({ ...row, content: reply, meta: out.meta ?? undefined }));
      setThreads(listChatThreads());
      void pollActionLifecycle();
      void pollJobLifecycle();
      void pollBrowserLifecycle();
    } catch (e) {
      const msg = formatChatError(e instanceof Error ? e.message : "Chat failed");
      if (isFocused()) setErr(msg);
      applyToAssistant((row) => ({ ...row, content: msg || "Request failed." }));
    } finally {
      streamAbortsRef.current.delete(turnThreadId);
      clearThreadBusy(turnThreadId);
      void refreshHealth();
      void refreshUsage();
      if (isFocused()) focusChatInput(inputRef.current);
    }
  };

  // §2/§5 — stop the focused thread's work only. Aborts its live stream and
  // cancels its durable agent job(s) best-effort (a running job that can't be
  // cancelled is left to finish honestly). Background threads keep running, and
  // navigation never reaches this path.
  const stopStreaming = useCallback(() => {
    const focused = activeThreadIdRef.current;
    streamAbortsRef.current.get(focused)?.abort();
    const thread = listChatThreads().find((t) => t.id === focused);
    for (const jobId of thread?.activeJobIds ?? []) {
      void cancelTrackedJob(jobId)
        .catch(() => undefined)
        .finally(() => {
          removeThreadJob(jobId);
          refreshJobBusy();
          setThreads(listChatThreads());
        });
    }
  }, [refreshJobBusy]);

  // §5 — keep a live reference to send so the queue dispatcher always calls the
  // latest closure without re-binding the effect on every render.
  const sendRef = useRef(send);
  sendRef.current = send;

  // Voice & audio surface. The transcript handler either fills the composer for
  // the operator to confirm/edit (push-to-talk) or auto-sends tagged surface=voice
  // (hands-free talk mode). Replies are spoken from the send pipeline above.
  const handleVoiceTranscript = useCallback<TranscriptHandler>((text, { autoSend }) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (autoSend) {
      void sendRef.current(trimmed, { surface: "voice" });
    } else {
      setInput((cur) => (cur.trim() ? `${cur} ${trimmed}` : trimmed));
      focusChatInput(inputRef.current);
    }
  }, []);
  const voice = useVoice(handleVoiceTranscript);
  voiceRef.current = voice;

  const queueInput = useCallback((text: string, kind: QueuedInputKind) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setQueued((q) => [...q, { id: id(), text: trimmed, kind }]);
  }, []);

  const dequeueInput = useCallback(
    (queuedId: string) => {
      setQueued((q) => {
        const item = q.find((x) => x.id === queuedId);
        if (item) {
          // Pull the queued text back into the editor (also satisfies abort-restore).
          setInput((cur) => (cur.trim() ? `${cur}\n${item.text}` : item.text));
          focusChatInput(inputRef.current);
        }
        return q.filter((x) => x.id !== queuedId);
      });
    },
    [],
  );

  // §5 — when the current turn finishes, dispatch the next queued input.
  // Steering notes are delivered before follow-ups.
  useEffect(() => {
    if (sending || queued.length === 0) return;
    const rank = (k: QueuedInputKind) => (k === "steering" ? 0 : 1);
    const next = [...queued].sort((a, b) => rank(a.kind) - rank(b.kind))[0];
    setQueued((q) => q.filter((x) => x.id !== next.id));
    void sendRef.current(next.text);
  }, [sending, queued]);

  // Sidebar collapse: hydrate from storage on mount.
  useEffect(() => {
    try {
      if (window.localStorage.getItem("aethos.chat.sidebarCollapsed") === "1") {
        setSidebarCollapsed(true);
      }
    } catch {
      /* storage unavailable — default to expanded */
    }
  }, []);

  // Persist collapse state across reloads.
  useEffect(() => {
    try {
      window.localStorage.setItem("aethos.chat.sidebarCollapsed", sidebarCollapsed ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed]);

  // Right-hand Runtime/context panel: hydrate, persist, and bind Ctrl+J / ⌘J to toggle it.
  useEffect(() => {
    try {
      if (window.localStorage.getItem("aethos.chat.contextOpen") === "0") setContextOpen(false);
    } catch {
      /* default open */
    }
  }, []);
  useEffect(() => {
    try {
      window.localStorage.setItem("aethos.chat.contextOpen", contextOpen ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [contextOpen]);
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey) return;
      if (e.key.toLowerCase() !== "j") return;
      e.preventDefault();
      setContextOpen((v) => !v);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  // Bind Ctrl+B / ⌘B to toggle the sidebar. On narrow viewports the sidebar is an
  // overlay (mobileNavOpen); on desktop it's the persistent column (sidebarCollapsed).
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!isSidebarToggleShortcut(e)) return;
      e.preventDefault();
      const isMobile =
        typeof window !== "undefined" &&
        typeof window.matchMedia === "function" &&
        window.matchMedia("(max-width: 960px)").matches;
      if (isMobile) {
        setMobileNavOpen((v) => !v);
      } else {
        setSidebarCollapsed((v) => !v);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div style={chatAppShellStyle} data-chat-scroll-root>
      <ChatSidebar
        mobileOpen={mobileNavOpen}
        collapsed={sidebarCollapsed}
        onCloseMobile={() => setMobileNavOpen(false)}
        threads={threads}
        activeThreadId={activeThreadId}
        busyThreadIds={[...new Set([...busyThreadIds, ...jobBusyThreadIds])]}
        onSelectThread={switchThread}
        onNewChat={handleNewChat}
        onDeleteThread={handleDeleteThread}
      />
      {sidebarCollapsed && (
        <button
          type="button"
          aria-label="Show sidebar"
          title="Show sidebar (Ctrl/⌘+B)"
          onClick={() => setSidebarCollapsed(false)}
          style={{
            position: "fixed",
            top: 14,
            left: 12,
            zIndex: 60,
            width: 32,
            height: 32,
            borderRadius: 8,
            border: "1px solid var(--aethos-border)",
            background: "var(--aethos-bg-card)",
            color: "var(--aethos-text)",
            cursor: "pointer",
            fontSize: 15,
            lineHeight: 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
          }}
        >
          ☰
        </button>
      )}
      {!contextOpen && (
        <button
          type="button"
          aria-label="Show runtime panel"
          title="Show runtime panel (Ctrl/⌘+J)"
          onClick={() => setContextOpen(true)}
          style={{
            position: "fixed",
            top: 14,
            right: 12,
            zIndex: 60,
            width: 32,
            height: 32,
            borderRadius: 8,
            border: "1px solid var(--aethos-border)",
            background: "var(--aethos-bg-card)",
            color: "var(--aethos-text)",
            cursor: "pointer",
            fontSize: 15,
            lineHeight: 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
          }}
        >
          ⊟
        </button>
      )}
      <div
        style={
          sidebarCollapsed
            ? { ...chatMainColumnStyle, paddingLeft: 52 } // clear the floating ☰ restore button
            : chatMainColumnStyle
        }
      >
        <ChatHeader
          health={health}
          onToggleMobileNav={() => setMobileNavOpen((v) => !v)}
          onToggleContext={() => setContextOpen((v) => !v)}
          contextOpen={contextOpen}
        />
        <UsageStrip usage={usage} fallbackModel={effectiveModel?.label ?? null} turnMeta={lastTurnMeta} />
        <div style={chatWorkspaceGridStyle} className="chat-workspace-grid">
          <div style={chatConversationColumnStyle}>
            <ChatTimeline
              messages={messages}
              sending={sending}
              err={err}
              liveUpdatesStatus={liveUpdatesStatus}
              showJumpToLatest={showJumpToLatest}
              scrollContainerRef={scrollContainerRef}
              messagesEndRef={messagesEndRef}
              onScroll={syncScrollState}
              onJumpToLatest={jumpToLatest}
            />
            <PwaInstallBanner />
            <ChatComposer
              input={input}
              sending={sending}
              mode={interactionMode}
              onModeChange={setInteractionMode}
              modelCatalogId={modelCatalogId}
              modelOptions={modelOptions}
              modelLoading={modelCatalogLoading}
              onModelChange={handleModelChange}
              onChange={setInput}
              onSend={() => void send()}
              inputRef={inputRef}
              queued={queued}
              onQueue={queueInput}
              onDequeue={dequeueInput}
              onStop={stopStreaming}
              voice={voice}
            />
          </div>
          {contextOpen ? (
            <ChatContextPanel messages={messages} health={health} effectiveModel={effectiveModel} />
          ) : null}
        </div>
      </div>
    </div>
  );
}
