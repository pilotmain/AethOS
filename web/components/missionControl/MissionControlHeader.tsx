"use client";

import { AccountMenu } from "@/components/auth/AccountMenu";
import { AppNav } from "@/components/AppNav";
import {
  mcButtonSecondaryStyle,
  missionControlHeaderStyle,
} from "@/lib/missionControl/layout";
import { flatNavDescription, flatNavLabel, modeNavSummary } from "@/lib/missionControl/flatNavigation";
import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import { useMissionControlTheme } from "@/lib/missionControl/theme";
import { type MissionControlView } from "@/lib/missionControl/views";

type Props = {
  activeView: MissionControlView;
  onRefreshAll: () => void;
  refreshing?: boolean;
  onToggleMobileNav?: () => void;
  mobileNavOpen?: boolean;
  mode: MissionControlMode;
  onModeChange: (mode: MissionControlMode) => void;
  quietMode?: boolean;
  onQuietModeChange?: (quiet: boolean) => void;
  focusMode?: boolean;
  onFocusModeChange?: (focus: boolean) => void;
};

const MODE_LABELS: Record<MissionControlMode, string> = {
  executive: "Executive",
  operator: "Operator",
  "deep-engineering": "Deep engineering",
};

export function MissionControlHeader({
  activeView,
  onRefreshAll,
  refreshing,
  onToggleMobileNav,
  mobileNavOpen,
  mode,
  onModeChange,
  quietMode,
  onQuietModeChange,
  focusMode,
  onFocusModeChange,
}: Props) {
  const { colors } = useMissionControlTheme();
  const { session } = useAuthScope();
  const modeSummary = modeNavSummary(mode, Boolean(session?.is_platform_owner));

  const pageTitle = flatNavLabel(activeView);
  const pageHint = flatNavDescription(activeView) || `${MODE_LABELS[mode]} view`;

  return (
    <header
      style={{
        ...missionControlHeaderStyle,
        borderBottom: "1px solid var(--aethos-glass-border)",
        background: "var(--aethos-glass-bg-strong)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        color: colors.text,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {onToggleMobileNav ? (
              <button
                type="button"
                className="mc-mobile-nav-toggle"
                onClick={onToggleMobileNav}
                style={{
                  ...mcButtonSecondaryStyle,
                  padding: "6px 10px",
                  display: "none",
                  borderColor: colors.border,
                  background: colors.bgCard,
                  color: colors.text,
                }}
                aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
              >
                ☰
              </button>
            ) : null}
            <div>
              <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>Mission Control</h1>
              <p style={{ margin: "6px 0 0", color: colors.textMuted, fontSize: 13 }}>
                {pageTitle} · {pageHint}
              </p>
            </div>
          </div>
          <AppNav active="mission-control" />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <AccountMenu />
          <span
            data-tour="mode-selector"
            style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}
            title={modeSummary.hint}
          >
            <select
              value={mode}
              onChange={(e) => onModeChange(e.target.value as MissionControlMode)}
              style={{
                ...mcButtonSecondaryStyle,
                padding: "6px 10px",
                fontSize: 12,
                borderColor: colors.border,
                background: colors.bgCard,
                color: colors.text,
              }}
              aria-label="Mission Control mode"
            >
              <option value="executive">Executive</option>
              <option value="operator">Operator</option>
              <option value="deep-engineering">Deep engineering</option>
            </select>
            <span style={{ fontSize: 10, color: colors.textMuted, paddingLeft: 2, maxWidth: 200 }}>
              {modeSummary.hint} · {modeSummary.count} panels
            </span>
          </span>
          {onQuietModeChange ? (
            <button
              type="button"
              onClick={() => onQuietModeChange(!quietMode)}
              style={{
                ...mcButtonSecondaryStyle,
                fontSize: 12,
                opacity: quietMode ? 1 : 0.85,
                borderColor: colors.border,
                background: colors.bgCard,
                color: colors.text,
              }}
            >
              {quietMode ? "Quiet on" : "Quiet"}
            </button>
          ) : null}
          {onFocusModeChange ? (
            <button
              type="button"
              onClick={() => onFocusModeChange(!focusMode)}
              style={{
                ...mcButtonSecondaryStyle,
                fontSize: 12,
                opacity: focusMode ? 1 : 0.85,
                borderColor: colors.border,
                background: colors.bgCard,
                color: colors.text,
              }}
            >
              {focusMode ? "Focus on" : "Focus"}
            </button>
          ) : null}
          <button
            type="button"
            onClick={onRefreshAll}
            disabled={refreshing}
            style={{ ...mcButtonSecondaryStyle, borderColor: colors.border, background: colors.bgCard, color: colors.text }}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>
    </header>
  );
}
