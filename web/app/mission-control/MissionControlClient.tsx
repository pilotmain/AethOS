"use client";

import { MissionControlShell } from "@/components/MissionControlShell";

/** Mission Control entry — loaded as a separate chunk from chat/login.
 * The theme provider is mounted once at the root layout (app/layout.tsx) so the
 * whole app — chat, workspace, Mission Control — themes consistently. */
export default function MissionControlClient() {
  return <MissionControlShell />;
}
