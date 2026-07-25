/** Mission Control layout tokens — wide-screen enterprise console. */

import type { CSSProperties } from "react";

export const MC_SIDEBAR_WIDTH = 240;
export const MC_CONTENT_MAX_WIDTH = 1400;

/** Default tokens — derived from the `--aethos-*` CSS variables in
 * `web/app/globals.css`, the single source of truth for the whole app. Every
 * value resolves to a token, so changing one variable restyles every page that
 * uses `mcColors` (the ~99 Mission Control / workspace components) and the
 * components that read `--aethos-*` directly. Prefer `useMissionControlTheme().colors`
 * inside MC UI that needs runtime theme switching. */
export const mcColors = {
  bg: "var(--aethos-bg)",
  bgElevated: "var(--aethos-bg-elevated)",
  bgCard: "var(--aethos-bg-card)",
  border: "var(--aethos-border)",
  borderSubtle: "var(--aethos-border-subtle)",
  text: "var(--aethos-text)",
  textMuted: "var(--aethos-text-muted)",
  textDim: "var(--aethos-text-dim)",
  green: "var(--aethos-ok)",
  amber: "var(--aethos-warn)",
  red: "var(--aethos-danger)",
  cyan: "var(--aethos-accent)",
  cyanDim: "var(--aethos-accent-dim)",
  violet: "var(--aethos-violet)",
  violetSoft: "var(--aethos-violet-soft)",
  violetDim: "var(--aethos-violet-dim)",
  glassBg: "var(--aethos-glass-bg)",
  glassBgStrong: "var(--aethos-glass-bg-strong)",
  glassBorder: "var(--aethos-glass-border)",
  navy: "var(--aethos-navy)",
  /** Legacy aliases used by MC panels */
  textBright: "var(--aethos-text-strong)",
  textSecondary: "var(--aethos-text-muted)",
  warning: "var(--aethos-warn)",
  panel: "var(--aethos-bg-card)",
  panelAlt: "var(--aethos-bg-elevated)",
  panelInset: "var(--aethos-bg-elevated)",
};

/** Full viewport shell with sidebar + main canvas. */
/** Deep-navy canvas with two faint corner glows (cyan top-left, violet top-right)
 * — the ambient backdrop the demo aesthetic is built on. */
export const mcShellBackground =
  "radial-gradient(1100px 560px at 12% -12%, rgba(34,211,238,0.07), transparent 60%)," +
  " radial-gradient(1000px 560px at 100% -8%, rgba(167,139,250,0.07), transparent 58%)," +
  " linear-gradient(160deg, var(--aethos-bg-deep) 0%, #070a12 55%, var(--aethos-bg) 100%)";

export const missionControlAppShellStyle: CSSProperties = {
  display: "flex",
  minHeight: "100vh",
  height: "100vh",
  width: "100%",
  background: mcShellBackground,
  color: mcColors.text,
};

export const missionControlSidebarStyle: CSSProperties = {
  width: MC_SIDEBAR_WIDTH,
  flexShrink: 0,
  display: "flex",
  flexDirection: "column",
  borderRight: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.35)",
  backdropFilter: "blur(8px)",
};

export const missionControlMainColumnStyle: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  minWidth: 0,
  minHeight: 0,
};

/** Legacy alias — wide main column, not narrow centered. */
export const missionControlPageRootStyle: CSSProperties = missionControlMainColumnStyle;

export const missionControlHeaderStyle: CSSProperties = {
  flexShrink: 0,
  padding: "20px 28px 16px",
  borderBottom: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
};

export const missionControlScrollMainStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  minHeight: 0,
  padding: "32px 36px 56px",
};

export const missionControlContentCanvasStyle: CSSProperties = {
  width: "100%",
  maxWidth: MC_CONTENT_MAX_WIDTH,
  margin: "0 auto",
};

/** Glassmorphic panel — translucent over the shell, soft glowing edge, blur.
 * This single style restyles ~100 Mission Control / workspace panels at once. */
export const mcCardStyle: CSSProperties = {
  width: "100%",
  borderRadius: 16,
  border: `1px solid ${mcColors.glassBorder}`,
  background: mcColors.glassBg,
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  boxShadow: "0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04)",
};

export const mcPanelSectionStyle: CSSProperties = {
  ...mcCardStyle,
  padding: 20,
  marginBottom: 20,
};

export const mcInputStyle: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 10,
  border: `1px solid ${mcColors.border}`,
  background: "rgba(0,0,0,0.35)",
  color: mcColors.text,
  fontSize: 13,
  outline: "none",
};

export const mcButtonPrimaryStyle: CSSProperties = {
  borderRadius: 10,
  padding: "8px 14px",
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
  border: "1px solid color-mix(in srgb, var(--aethos-ok) 35%, transparent)",
  background: "color-mix(in srgb, var(--aethos-ok) 14%, transparent)",
  color: "var(--aethos-ok)",
};

export const mcButtonSecondaryStyle: CSSProperties = {
  borderRadius: 10,
  padding: "8px 14px",
  fontSize: 13,
  fontWeight: 500,
  cursor: "pointer",
  border: `1px solid ${mcColors.border}`,
  background: "rgba(255,255,255,0.04)",
  color: mcColors.text,
};

export const mcButtonDangerStyle: CSSProperties = {
  borderRadius: 10,
  padding: "6px 12px",
  fontSize: 12,
  cursor: "pointer",
  border: "1px solid color-mix(in srgb, var(--aethos-danger) 35%, transparent)",
  background: "transparent",
  color: "var(--aethos-danger)",
};

/** Shared status vocabulary (§4) — one meaning for ok/warn/danger/running/idle
 * on every page. All resolve to --aethos-* tokens via mcColors. */
export type McStatusTone = "ok" | "warn" | "danger" | "running" | "idle";

export function mcStatusColor(tone: McStatusTone): string {
  switch (tone) {
    case "ok":
      return mcColors.green;
    case "warn":
      return mcColors.amber;
    case "danger":
      return mcColors.red;
    case "running":
      return mcColors.cyan;
    default:
      return mcColors.textDim;
  }
}

/** Translucent fill/border from any token color (replaces `${hex}44` concat,
 * which breaks once the base color is a CSS var()). */
export function mcAlpha(color: string, pct: number): string {
  return `color-mix(in srgb, ${color} ${pct}%, transparent)`;
}

/** Shared section eyebrow header — same rhythm across every surface. */
export const mcSectionHeaderStyle: CSSProperties = {
  margin: 0,
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: "0.04em",
  textTransform: "uppercase",
  color: mcColors.textDim,
};

/** Shared chip/badge — pass a status tone for consistent ok/warn/danger styling. */
export function mcChipStyle(tone: McStatusTone = "idle"): CSSProperties {
  const c = mcStatusColor(tone);
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "2px 10px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 600,
    color: c,
    border: `1px solid ${mcAlpha(c, 35)}`,
    background: mcAlpha(c, 12),
  };
}

/** Shared empty-state text — a short line, optionally followed by one action. */
export const mcEmptyStateStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  color: mcColors.textMuted,
  lineHeight: 1.5,
};

export const artifactReportPreStyle: CSSProperties = {
  margin: 0,
  whiteSpace: "pre-wrap",
  fontSize: 12,
  padding: 10,
  borderRadius: 8,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
};

/** Cyan→violet gradient text — for the logo and hero headings. */
export const mcGradientTextStyle: CSSProperties = {
  backgroundImage: "var(--aethos-accent-grad)",
  WebkitBackgroundClip: "text",
  backgroundClip: "text",
  WebkitTextFillColor: "transparent",
  color: "transparent",
};

/** Soft outer glow in the cyan or violet accent — for active/hero surfaces. */
export function mcGlow(tone: "cyan" | "violet" = "cyan"): string {
  return tone === "violet" ? "var(--aethos-glow-violet)" : "var(--aethos-glow-cyan)";
}

export const MISSION_CONTROL_SCROLL_ROOT_ATTR = "data-mc-scroll-root";
export const MISSION_CONTROL_SCROLL_MAIN_ATTR = "data-mc-scroll-main";
