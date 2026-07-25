/** Chat health — independent from Mission Control panel state (Phase 3 adds MC). */

export type ChatHealth = {
  chatReady: boolean;
  connectionLabel: string;
  panelState: string;
};

export function deriveChatHealth(payload: {
  chat_ready: boolean;
  label: string;
  panel: string;
}): ChatHealth {
  return {
    chatReady: payload.chat_ready,
    connectionLabel: payload.label,
    panelState: payload.panel,
  };
}

/** Panel degradation must not disable send when chat_ready is true. */
export function canSendChat(health: ChatHealth): boolean {
  return health.chatReady;
}
