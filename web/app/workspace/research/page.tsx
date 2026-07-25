"use client";

import Link from "next/link";

import { AppNav } from "@/components/AppNav";
import { DeepResearchPanel } from "@/components/missionControl/DeepResearchPanel";
import { mcButtonSecondaryStyle, mcColors } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";

export default function WorkspaceResearchPage() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Research</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
              Deep research with evidence scoring and replayable reports.
            </p>
            <AppNav active="research" />
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link href="/" style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              ← Chat
            </Link>
            <Link href={missionControlHref("home")} style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              Mission Control
            </Link>
          </div>
        </div>
        <DeepResearchPanel embedded />
      </div>
    </div>
  );
}
