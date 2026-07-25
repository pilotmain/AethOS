/** FIX 130 — operator session context for Mission Control (read-only). */

import { useEffect, useState } from "react";

import { getOrCreateChatSessionId } from "@/lib/chat/actionLifecycleBridge";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

export type OperatorContext = {
  sessionId: string;
  channel: "mission_control";
  operatorMode: MissionControlMode;
  surface: "cross-lane-operations";
};

export function resolveOperatorSessionId(explicit?: string): string {
  if (explicit?.trim()) return explicit.trim();
  return getOrCreateChatSessionId();
}

export function buildOperatorContext(
  sessionId: string,
  operatorMode: MissionControlMode = "operator",
): OperatorContext {
  return {
    sessionId,
    channel: "mission_control",
    operatorMode,
    surface: "cross-lane-operations",
  };
}

/** Hydrates the chat session id from sessionStorage (same id as ChatShell). */
export function useOperatorSession(explicitSessionId?: string): {
  context: OperatorContext | null;
  hydrated: boolean;
} {
  const [hydrated, setHydrated] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    setSessionId(resolveOperatorSessionId(explicitSessionId));
    setHydrated(true);
  }, [explicitSessionId]);

  if (!hydrated || sessionId == null) {
    return { context: null, hydrated: false };
  }

  return {
    hydrated: true,
    context: buildOperatorContext(sessionId),
  };
}
