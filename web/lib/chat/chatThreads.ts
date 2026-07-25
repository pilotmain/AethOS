/** Multi-chat threads — each thread maps to one backend session_id. */

import type { CachedMessage } from "@/lib/chat/types";

export type ChatThread = {
  id: string;
  sessionId: string;
  title: string;
  messages: CachedMessage[];
  createdAt: number;
  updatedAt: number;
  /** §4 session tree — lineage when this thread was forked/cloned from another. */
  forkedFromThreadId?: string;
  forkedFromMessageId?: string;
  /** Durable agent jobs whose turn started in this thread and may still be
   * running server-side. Persisted so a reload / tab reopen reconnects to the
   * job by id and the thread shows a "working…" indicator until it finishes. */
  activeJobIds?: string[];
};

import { scopedStorageKey } from "@/lib/auth/userScope";

const THREADS_KEY_BASE = "aethos_chat_threads_v1";
const ACTIVE_THREAD_KEY_BASE = "aethos_chat_active_thread_id";
const LEGACY_MESSAGES_KEY = "aethos_chat_messages";
const LEGACY_SESSION_KEY = "aethos_chat_session_id";

function threadsKey(): string {
  return scopedStorageKey(THREADS_KEY_BASE);
}

function activeThreadKey(): string {
  return scopedStorageKey(ACTIVE_THREAD_KEY_BASE);
}

/**
 * The ACTIVE thread pointer is per-tab/window (sessionStorage), NOT shared
 * (localStorage). The thread *list* stays in localStorage so every window can see
 * and switch to any conversation, but each window remembers its OWN active thread.
 * This stops a new window from inheriting another window's conversation (§4 — no
 * cross-window bleed) and keeps the Canvas bound to the same session the visible
 * chat uses. sessionStorage survives reloads of the same tab but is isolated
 * between tabs/windows, which is exactly the scope we want.
 */
function readActivePointer(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(activeThreadKey());
  } catch {
    return null;
  }
}

function writeActivePointer(threadId: string): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(activeThreadKey(), threadId);
  } catch {
    /* quota / disabled */
  }
}

function newId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function newSessionId(): string {
  return `sess-${Math.random().toString(36).slice(2, 10)}`;
}

function readStore(): ChatThread[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(threadsKey());
    if (!raw) return migrateLegacyThread();
    const parsed = JSON.parse(raw) as ChatThread[];
    return Array.isArray(parsed) ? parsed : migrateLegacyThread();
  } catch {
    return migrateLegacyThread();
  }
}

function writeStore(threads: ChatThread[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(threadsKey(), JSON.stringify(threads.slice(-40)));
  } catch {
    /* quota */
  }
}

function migrateLegacyThread(): ChatThread[] {
  if (typeof window === "undefined") return [createEmptyThread("Conversation")];
  try {
    const legacyMessagesRaw = sessionStorage.getItem(LEGACY_MESSAGES_KEY);
    const legacySession = sessionStorage.getItem(LEGACY_SESSION_KEY) || newSessionId();
    const messages = legacyMessagesRaw
      ? ((JSON.parse(legacyMessagesRaw) as CachedMessage[]) ?? [])
      : [];
    const thread: ChatThread = {
      id: newId("thread"),
      sessionId: legacySession,
      title: titleFromMessages(messages) || "Conversation",
      messages: Array.isArray(messages) ? messages : [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    writeStore([thread]);
    writeActivePointer(thread.id);
    sessionStorage.setItem(LEGACY_SESSION_KEY, thread.sessionId);
    return [thread];
  } catch {
    const thread = createEmptyThread("Conversation");
    writeStore([thread]);
    return [thread];
  }
}

export function titleFromMessages(messages: CachedMessage[]): string {
  const first = messages.find((m) => m.role === "user" && (m.content || "").trim());
  if (!first) return "New chat";
  const text = first.content.trim().replace(/\s+/g, " ");
  return text.length > 48 ? `${text.slice(0, 48)}…` : text;
}

export function createEmptyThread(title = "New chat"): ChatThread {
  const sessionId = newSessionId();
  return {
    id: newId("thread"),
    sessionId,
    title,
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

export function listChatThreads(): ChatThread[] {
  const rows = readStore();
  return [...rows].sort((a, b) => b.updatedAt - a.updatedAt);
}

export function getActiveThreadId(): string {
  if (typeof window === "undefined") return "";
  const stored = readActivePointer();
  const threads = readStore();
  if (stored && threads.some((t) => t.id === stored)) return stored;
  // No per-tab pointer → fresh window/tab (e.g. after login). Reuse an existing
  // empty "New chat" instead of piling up a fresh one on every visit. Empty threads
  // hold no conversation, so adopting one can't leak another window's chat — and we
  // still never adopt a thread that already has messages.
  const empty = threads.find(
    (t) => t.messages.length === 0 && (t.title === "New chat" || !t.title),
  );
  if (empty) {
    writeActivePointer(empty.id);
    return empty.id;
  }
  const created = createEmptyThread();
  writeStore([created, ...threads]);
  writeActivePointer(created.id);
  return created.id;
}

export function getActiveThread(): ChatThread {
  const id = getActiveThreadId();
  const thread = readStore().find((t) => t.id === id);
  if (thread) return thread;
  const created = createEmptyThread();
  writeStore([created]);
  writeActivePointer(created.id);
  syncLegacySession(created);
  return created;
}

export function selectChatThread(threadId: string): ChatThread | null {
  const threads = readStore();
  const thread = threads.find((t) => t.id === threadId);
  if (!thread) return null;
  writeActivePointer(thread.id);
  syncLegacySession(thread);
  return thread;
}

export function createChatThread(title = "New chat"): ChatThread {
  const thread = createEmptyThread(title);
  const threads = [thread, ...readStore()];
  writeStore(threads);
  writeActivePointer(thread.id);
  syncLegacySession(thread);
  return thread;
}

/**
 * @deprecated Writes to whatever thread is globally "active" (the shared
 * localStorage pointer), which bleeds messages across tabs/windows. Use the
 * thread-id-scoped {@link updateThreadMessages} keyed on the window's own
 * activeThreadId instead. Retained only for legacy/test callers.
 */
export function updateActiveThreadMessages(messages: CachedMessage[]): ChatThread {
  const activeId = getActiveThreadId();
  const trimmed = messages.slice(-80);
  const threads = readStore().map((t) => {
    if (t.id !== activeId) return t;
    return {
      ...t,
      messages: trimmed,
      title: t.title === "New chat" || !t.title ? titleFromMessages(trimmed) : t.title,
      updatedAt: Date.now(),
    };
  });
  writeStore(threads);
  const updated = threads.find((t) => t.id === activeId)!;
  syncLegacySession(updated);
  try {
    sessionStorage.setItem(LEGACY_MESSAGES_KEY, JSON.stringify(trimmed));
  } catch {
    /* quota */
  }
  return updated;
}

/** Messages stored for a specific thread (authoritative store read). */
export function getThreadMessages(threadId: string): CachedMessage[] {
  const thread = readStore().find((t) => t.id === threadId);
  return thread ? thread.messages : [];
}

/**
 * Thread-id-scoped message read. Prefer this over the global-active read path so
 * a window always reads the thread it is actually displaying (§4 — no bleed).
 */
export function readThreadMessages(threadId: string): CachedMessage[] {
  return getThreadMessages(threadId);
}

/** Persist messages to a SPECIFIC thread (not necessarily the active one).
 *
 * Concurrency: a turn started in thread A must keep writing to A's store even
 * after the operator switches to thread B. We only mirror the legacy/session
 * cache when the target thread is the active (visible) one, so a background
 * turn never clobbers the visible thread's cache. */
export function updateThreadMessages(threadId: string, messages: CachedMessage[]): ChatThread | null {
  const trimmed = messages.slice(-80);
  let found = false;
  const threads = readStore().map((t) => {
    if (t.id !== threadId) return t;
    found = true;
    return {
      ...t,
      messages: trimmed,
      title: t.title === "New chat" || !t.title ? titleFromMessages(trimmed) : t.title,
      updatedAt: Date.now(),
    };
  });
  if (!found) return null;
  writeStore(threads);
  const updated = threads.find((t) => t.id === threadId)!;
  if (threadId === getActiveThreadId()) {
    syncLegacySession(updated);
    try {
      sessionStorage.setItem(LEGACY_MESSAGES_KEY, JSON.stringify(trimmed));
    } catch {
      /* quota */
    }
  }
  return updated;
}

/** Attach a durable job to a thread (deduped). */
export function addThreadJob(threadId: string, jobId: string): void {
  if (!threadId || !jobId) return;
  const threads = readStore().map((t) => {
    if (t.id !== threadId) return t;
    const existing = Array.isArray(t.activeJobIds) ? t.activeJobIds : [];
    if (existing.includes(jobId)) return t;
    return { ...t, activeJobIds: [...existing, jobId].slice(-12) };
  });
  writeStore(threads);
}

/** Detach a finished/cancelled job from whichever thread owns it. */
export function removeThreadJob(jobId: string): void {
  if (!jobId) return;
  let changed = false;
  const threads = readStore().map((t) => {
    const existing = Array.isArray(t.activeJobIds) ? t.activeJobIds : [];
    if (!existing.includes(jobId)) return t;
    changed = true;
    return { ...t, activeJobIds: existing.filter((id) => id !== jobId) };
  });
  if (changed) writeStore(threads);
}

/** Thread ids that currently have at least one active durable job. */
export function threadsWithActiveJobs(): string[] {
  return readStore()
    .filter((t) => Array.isArray(t.activeJobIds) && t.activeJobIds.length > 0)
    .map((t) => t.id);
}

/** All durable job ids still attached to any thread (re-tracked on mount). */
export function allActiveThreadJobIds(): string[] {
  const ids: string[] = [];
  for (const t of readStore()) {
    if (Array.isArray(t.activeJobIds)) ids.push(...t.activeJobIds);
  }
  return [...new Set(ids)];
}

export function deleteChatThread(threadId: string): ChatThread | null {
  let threads = readStore().filter((t) => t.id !== threadId);
  if (threads.length === 0) {
    const fresh = createEmptyThread();
    threads = [fresh];
  }
  writeStore(threads);
  const activeId = getActiveThreadId();
  if (activeId === threadId || !threads.some((t) => t.id === activeId)) {
    const next = threads[0]!;
    writeActivePointer(next.id);
    syncLegacySession(next);
    return next;
  }
  return threads.find((t) => t.id === getActiveThreadId()) ?? null;
}

export function getActiveSessionId(): string {
  return getActiveThread().sessionId;
}

/** §4 — indexed outline of the active thread so the operator can pick a branch point. */
export function sessionTreeOutline(thread: ChatThread): string {
  if (thread.messages.length === 0) return "This thread has no messages yet.";
  const lines = [`Session tree · ${thread.messages.length} messages (use /fork <n> to branch):`];
  thread.messages.forEach((m, i) => {
    const snippet = (m.content || "").trim().replace(/\s+/g, " ").slice(0, 64);
    lines.push(`  ${i + 1}. [${m.role}] ${snippet}${snippet.length >= 64 ? "…" : ""}`);
  });
  if (thread.forkedFromThreadId) {
    lines.push(`(branched from an earlier thread)`);
  }
  return lines.join("\n");
}

/** §4 — fork a new independent branch from the active thread up to 1-based index. */
export function forkActiveThreadAtIndex(index1Based: number): ChatThread | null {
  const active = getActiveThread();
  const idx = index1Based - 1;
  if (idx < 0 || idx >= active.messages.length) return null;
  const slice = active.messages.slice(0, idx + 1).map((m) => ({ ...m }));
  const fork: ChatThread = {
    id: newId("thread"),
    sessionId: newSessionId(),
    title: `Fork @${index1Based}: ${active.title}`.slice(0, 60),
    messages: slice,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    forkedFromThreadId: active.id,
    forkedFromMessageId: active.messages[idx]?.id,
  };
  const threads = [fork, ...readStore()];
  writeStore(threads);
  writeActivePointer(fork.id);
  syncLegacySession(fork);
  return fork;
}

/** §4 — clone the entire active branch into a new independent thread. */
export function cloneActiveThread(): ChatThread {
  const active = getActiveThread();
  const clone: ChatThread = {
    id: newId("thread"),
    sessionId: newSessionId(),
    title: `Copy: ${active.title}`.slice(0, 60),
    messages: active.messages.map((m) => ({ ...m })),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    forkedFromThreadId: active.id,
  };
  const threads = [clone, ...readStore()];
  writeStore(threads);
  writeActivePointer(clone.id);
  syncLegacySession(clone);
  return clone;
}

/** §6 — escape user/assistant text for safe embedding in exported HTML. */
function escapeHtml(s: string): string {
  return (s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** §6 — render a session to a self-contained dark-themed HTML document.
 * Privacy-first: no external assets or upload; tokens are inlined so the file
 * opens correctly offline in any browser. */
export function buildSessionExportHtml(thread: ChatThread): string {
  const when = new Date().toLocaleString();
  const rows = thread.messages
    .filter((m) => (m.content || "").trim())
    .map((m) => {
      const body = escapeHtml(m.content || "").replace(/\n/g, "<br>");
      return `<div class="msg ${escapeHtml(m.role)}"><div class="role">${escapeHtml(
        m.role,
      )}</div><div class="body">${body}</div></div>`;
    })
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AethOS session — ${escapeHtml(thread.title || "Conversation")}</title>
<style>
  :root { color-scheme: dark; --bg:#050508; --surface:rgba(255,255,255,0.03); --border:rgba(255,255,255,0.1); --text:#e4e4e7; --muted:#a1a1aa; --accent:#22d3ee; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.55; }
  .wrap { max-width:820px; margin:0 auto; padding:32px 20px 64px; }
  header { border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:24px; }
  h1 { font-size:18px; margin:0 0 6px; }
  .meta { color:var(--muted); font-size:12px; }
  .msg { padding:14px 16px; border:1px solid var(--border); border-radius:12px; margin-bottom:12px; background:var(--surface); }
  .role { font-size:11px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }
  .msg.user .role { color:var(--accent); }
  .body { font-size:14px; white-space:normal; word-wrap:break-word; }
  footer { margin-top:32px; color:var(--muted); font-size:11px; text-align:center; }
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>${escapeHtml(thread.title || "Conversation")}</h1>
      <div class="meta">AethOS session export · ${escapeHtml(when)} · ${thread.messages.length} messages</div>
    </header>
    ${rows || '<div class="meta">No messages.</div>'}
    <footer>Exported locally from AethOS — no data left this machine.</footer>
  </div>
</body>
</html>`;
}

/** §6 — plain-text shareable summary for clipboard. */
export function buildSessionSummaryText(thread: ChatThread): string {
  const lines = [`AethOS session: ${thread.title || "Conversation"}`, ""];
  for (const m of thread.messages) {
    const body = (m.content || "").trim();
    if (!body) continue;
    lines.push(`[${m.role}] ${body}`);
    lines.push("");
  }
  return lines.join("\n").trim();
}

export function exportFilename(thread: ChatThread): string {
  const slug = (thread.title || "session")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40) || "session";
  return `aethos-${slug}.html`;
}

type ActiveSessionListener = (sessionId: string) => void;
const activeSessionListeners = new Set<ActiveSessionListener>();

/** Subscribe to the active chat thread's backend session_id (same id chat POST uses). */
export function subscribeActiveChatSessionId(listener: ActiveSessionListener): () => void {
  activeSessionListeners.add(listener);
  try {
    listener(getActiveSessionId());
  } catch {
    listener("default");
  }
  return () => activeSessionListeners.delete(listener);
}

function notifyActiveSessionListeners(sessionId: string): void {
  for (const listener of activeSessionListeners) {
    try {
      listener(sessionId);
    } catch {
      /* listener */
    }
  }
}

function syncLegacySession(thread: ChatThread): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(LEGACY_SESSION_KEY, thread.sessionId);
    sessionStorage.setItem(LEGACY_MESSAGES_KEY, JSON.stringify(thread.messages.slice(-80)));
    notifyActiveSessionListeners(thread.sessionId);
  } catch {
    /* quota */
  }
}

/** Merge server thread index into local storage (server wins when newer). */
export function mergeServerThreadsIntoLocal(
  rows: {
    session_id: string;
    title: string;
    created_at?: number;
    updated_at?: number;
    messages?: CachedMessage[];
  }[],
): void {
  if (typeof window === "undefined" || rows.length === 0) return;
  const local = readStore();
  const bySession = new Map(local.map((t) => [t.sessionId, t]));
  const merged: ChatThread[] = [];

  for (const row of rows) {
    const existing = bySession.get(row.session_id);
    const serverUpdated = row.updated_at ?? 0;
    const localUpdated = existing?.updatedAt ?? 0;
    if (serverUpdated >= localUpdated || !existing) {
      merged.push({
        id: existing?.id ?? newId("thread"),
        sessionId: row.session_id,
        title: row.title || existing?.title || "New chat",
        messages: Array.isArray(row.messages) ? row.messages.slice(-80) : existing?.messages ?? [],
        createdAt: row.created_at ?? existing?.createdAt ?? Date.now(),
        updatedAt: serverUpdated || Date.now(),
        // Durable job attachments are local-only state; never let a server
        // thread sync drop an in-flight job from its originating thread.
        activeJobIds: existing?.activeJobIds,
      });
      bySession.delete(row.session_id);
    } else if (existing) {
      merged.push(existing);
      bySession.delete(row.session_id);
    }
  }

  for (const leftover of bySession.values()) {
    merged.push(leftover);
  }

  merged.sort((a, b) => b.updatedAt - a.updatedAt);
  writeStore(merged);
  // Repair ONLY a stale pointer — one that is set but points to a thread that no
  // longer exists after the merge. A fresh window with NO pointer must NOT adopt
  // the most-recent server thread here: that is exactly the cross-window bleed
  // (§4). getActiveThread() will mint this window its own empty thread instead.
  const activeId = readActivePointer();
  if (activeId && !merged.some((t) => t.id === activeId) && merged[0]) {
    writeActivePointer(merged[0].id);
    syncLegacySession(merged[0]);
  }
}
