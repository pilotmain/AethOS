"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import {
  filterAdvancedSectionsForMode,
  filterFlatGroupsForMode,
  filterNavSearch,
  isAdvancedSettingsView,
  type FlatNavExternalId,
} from "@/lib/missionControl/flatNavigation";
import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import { AethosLogo } from "@/components/branding/AethosLogo";
import { mcGradientTextStyle } from "@/lib/missionControl/layout";
import { TOUR_ANCHORS } from "@/lib/onboarding/walkthrough";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import { useMissionControlTheme, type McThemePreference } from "@/lib/missionControl/theme";
import { type MissionControlView } from "@/lib/missionControl/views";

/** Stable tour hook for the panels the walkthrough points at. */
function tourAnchorFor(id: string): string | undefined {
  switch (id) {
    case "chat":
      return TOUR_ANCHORS.navChat;
    case "agent-orchestration":
      return TOUR_ANCHORS.navAgents;
    case "agent-comms":
      return TOUR_ANCHORS.navMultiAgent;
    case "arbiter-panel":
      return TOUR_ANCHORS.navArbiter;
    case "blind-model-eval":
      return TOUR_ANCHORS.navCompare;
    case "deep-research":
      return TOUR_ANCHORS.navResearch;
    case "provider-inventory":
      return TOUR_ANCHORS.navProviders;
    case "approval-inbox":
      return TOUR_ANCHORS.navApprovals;
    case "audit-logs":
      return TOUR_ANCHORS.navAudit;
    default:
      return undefined;
  }
}

type Props = {
  active: MissionControlView;
  onNavigate: (view: MissionControlView) => void;
  mode?: MissionControlMode;
  /** Force the Advanced tray open (e.g. while the tour spotlights a panel inside it). */
  forceAdvancedOpen?: boolean;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
};

function NavButton({
  label,
  icon,
  hint,
  active,
  onClick,
  colors,
  indent,
  dataTour,
}: {
  label: string;
  icon?: string;
  hint?: string;
  active: boolean;
  onClick: () => void;
  colors: ReturnType<typeof useMissionControlTheme>["colors"];
  indent?: boolean;
  dataTour?: string;
}) {
  return (
    <button
      type="button"
      className="mc-nav-item"
      data-tour={dataTour}
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        width: "100%",
        textAlign: "left",
        padding: indent ? "6px 10px 6px 22px" : "8px 10px",
        marginBottom: 2,
        borderRadius: 10,
        border: "none",
        cursor: "pointer",
        fontSize: indent ? 12 : 13,
        fontWeight: active ? 600 : 500,
        color: active ? colors.cyan : colors.textNavInactive,
        background: active ? "var(--aethos-accent-grad-soft)" : "transparent",
        boxShadow: active ? "inset 3px 0 0 var(--aethos-accent), 0 0 18px -6px rgba(34,211,238,0.5)" : "none",
        transition: "background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease",
      }}
    >
      {icon ? (
        <span style={{ width: 18, flexShrink: 0, opacity: active ? 1 : 0.72, fontSize: 14, lineHeight: 1.4 }}>
          {icon}
        </span>
      ) : null}
      <span style={{ flex: 1 }}>
        <span>{label}</span>
        {active && hint ? (
          <span style={{ display: "block", fontSize: 10, color: colors.textMuted, marginTop: 3, fontWeight: 400 }}>
            {hint}
          </span>
        ) : null}
      </span>
    </button>
  );
}

export function MissionControlSidebar({
  active,
  onNavigate,
  mode = "operator",
  forceAdvancedOpen = false,
  mobileOpen,
  onCloseMobile,
}: Props) {
  const { colors, themePreference, setThemePreference } = useMissionControlTheme();
  const { session } = useAuthScope();
  const isPlatformOwner = Boolean(session?.is_platform_owner);
  const [searchQuery, setSearchQuery] = useState("");
  const [advancedOpen, setAdvancedOpen] = useState(isAdvancedSettingsView(active));
  const showAdvanced = advancedOpen || forceAdvancedOpen;

  const searchResults = useMemo(
    () => filterNavSearch(searchQuery, isPlatformOwner),
    [searchQuery, isPlatformOwner],
  );

  // The chosen mode is the source of truth for what the sidebar shows — keeping
  // the dropdown's promise (Executive / Operator / Deep engineering) honest.
  const navGroups = useMemo(() => filterFlatGroupsForMode(mode), [mode]);
  const advancedSections = useMemo(
    () => filterAdvancedSectionsForMode(mode, isPlatformOwner),
    [mode, isPlatformOwner],
  );

  const cycleTheme = () => {
    const order: McThemePreference[] = ["dark", "light", "system"];
    const idx = order.indexOf(themePreference);
    setThemePreference(order[(idx + 1) % order.length]);
  };

  const handleMcNavigate = (view: MissionControlView) => {
    onNavigate(view);
    onCloseMobile?.();
    setSearchQuery("");
  };

  const handleExternal = (href: string) => {
    onCloseMobile?.();
    setSearchQuery("");
  };

  const handleSearchPick = (id: MissionControlView | FlatNavExternalId, href?: string) => {
    if (href) {
      handleExternal(href);
      return;
    }
    if (id === "theme") {
      cycleTheme();
      return;
    }
    handleMcNavigate(id as MissionControlView);
  };

  return (
    <aside
      className="mc-sidebar"
      style={{
        width: 240,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        borderRight: `1px solid ${colors.borderSubtle}`,
        background: colors.sidebarBg,
      }}
      data-mobile-open={mobileOpen ? "true" : undefined}
      data-mc-nav="flat"
    >
      <div style={{ padding: "20px 16px 12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <AethosLogo size={26} />
          <div
            style={{
              fontSize: 18,
              fontWeight: 800,
              letterSpacing: "0.14em",
              width: "fit-content",
              ...mcGradientTextStyle,
            }}
          >
            AETHOS
          </div>
        </div>
        <div style={{ fontSize: 13, fontWeight: 600, marginTop: 4, color: colors.textMuted }}>Mission Control</div>
      </div>

      <div style={{ padding: "0 12px 12px" }}>
        <input
          type="search"
          data-tour={TOUR_ANCHORS.navSearch}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search panels…"
          aria-label="Search Mission Control panels"
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "8px 10px",
            borderRadius: 10,
            border: `1px solid ${colors.borderSubtle}`,
            background: colors.bgCard,
            color: colors.text,
            fontSize: 13,
          }}
        />
      </div>

      <nav style={{ flex: 1, overflowY: "auto", padding: "0 8px 16px" }}>
        {searchQuery.trim() ? (
          <div>
            {searchResults.length === 0 ? (
              <p style={{ fontSize: 12, color: colors.textMuted, padding: "8px 10px" }}>No matching panels.</p>
            ) : (
              searchResults.slice(0, 24).map((item) => (
                <NavButton
                  key={String(item.id)}
                  label={item.label}
                  hint={item.section}
                  active={item.id === active}
                  onClick={() => {
                    if (item.href) {
                      window.location.href = item.href;
                      handleExternal(item.href);
                      return;
                    }
                    if (item.id === "theme") {
                      cycleTheme();
                      return;
                    }
                    handleSearchPick(item.id, item.href);
                  }}
                  colors={colors}
                />
              ))
            )}
          </div>
        ) : (
          <>
            {navGroups.map((group) => (
              <div key={group.id} style={{ marginBottom: 8 }}>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: colors.textMuted,
                    padding: "12px 10px 6px",
                  }}
                >
                  {group.label}
                </div>
                {group.items.map((item) => {
                  if (item.id === "theme") {
                    return (
                      <NavButton
                        key={item.id}
                        label={item.label}
                        icon={item.icon}
                        hint={`${item.description} · ${themePreference}`}
                        active={false}
                        onClick={cycleTheme}
                        colors={colors}
                      />
                    );
                  }
                  if (item.href) {
                    const isActive = false;
                    return (
                      <Link
                        key={item.id}
                        href={item.href}
                        data-tour={tourAnchorFor(item.id as string)}
                        onClick={() => handleExternal(item.href!)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          padding: "8px 10px",
                          marginBottom: 2,
                          borderRadius: 10,
                          textDecoration: "none",
                          fontSize: 13,
                          fontWeight: isActive ? 600 : 500,
                          color: colors.textNavInactive,
                        }}
                      >
                        <span style={{ width: 18, fontSize: 14 }}>{item.icon}</span>
                        <span>{item.label}</span>
                      </Link>
                    );
                  }
                  return (
                    <NavButton
                      key={item.id}
                      label={item.label}
                      icon={item.icon}
                      hint={item.description}
                      active={active === item.id}
                      onClick={() => handleMcNavigate(item.id as MissionControlView)}
                      colors={colors}
                      dataTour={tourAnchorFor(item.id as string)}
                    />
                  );
                })}
              </div>
            ))}

            {advancedSections.length > 0 ? (
              <div style={{ marginTop: 8, borderTop: `1px solid ${colors.borderSubtle}`, paddingTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setAdvancedOpen((v) => !v)}
                  style={{
                    display: "flex",
                    width: "100%",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 10px",
                    border: "none",
                    background: "transparent",
                    cursor: "pointer",
                    color: colors.textMuted,
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                  }}
                >
                  <span>Advanced settings</span>
                  <span>{showAdvanced ? "▾" : "▸"}</span>
                </button>
                {showAdvanced ? (
                  <div>
                    {advancedSections.map((section) => (
                      <div key={section.title}>
                        <div
                          style={{
                            fontSize: 10,
                            color: colors.textDim,
                            padding: "8px 10px 4px",
                            fontWeight: 600,
                          }}
                        >
                          {section.title}
                        </div>
                        {section.items.map((item) => (
                          <NavButton
                            key={item.id}
                            label={item.label}
                            icon={item.icon}
                            hint={item.description}
                            active={active === item.id}
                            onClick={() => handleMcNavigate(item.id as MissionControlView)}
                            colors={colors}
                            indent
                            dataTour={tourAnchorFor(item.id as string)}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </>
        )}
      </nav>
    </aside>
  );
}
