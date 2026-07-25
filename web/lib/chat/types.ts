/** Shared chat message types (web client). */

/**
 * §1/§3 live progress narration — a single step or thought emitted by the agent
 * tool loop and streamed over /chat/stream. Steps share an `id` across their
 * running -> done/failed lifecycle so the UI can update one row in place.
 */
export type ChatProgressEvent = {
  type: "step" | "thought";
  id?: string;
  tool?: string;
  action?: string;
  status?: "running" | "done" | "failed";
  summary?: string;
  text?: string;
};

export type CachedMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  /** §4 session tree — id of the message this one was produced in reply to. */
  parentId?: string;
  event_type?: string;
  action_id?: string;
  meta?: Record<string, unknown>;
  /** §3 live activity feed — ordered step/thought events for this turn. */
  progress?: ChatProgressEvent[];
};
