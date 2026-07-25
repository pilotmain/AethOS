/** Operational palette — dark & light cognitive color systems (Phase 10.1.5.10). */

export type McResolvedTheme = "dark" | "light";
export type McThemePreference = "dark" | "light" | "system";
export type McAccessibilityMode =
  | "standard"
  | "high-readability"
  | "reduced-atmosphere"
  | "focus";

export type McColorTokens = {
  bg: string;
  bgElevated: string;
  bgCard: string;
  bgSurfacePrimary: string;
  bgSurfaceSolid: string;
  border: string;
  borderSubtle: string;
  text: string;
  textStrong: string;
  textMuted: string;
  textDim: string;
  textNavInactive: string;
  green: string;
  amber: string;
  red: string;
  cyan: string;
  navy: string;
  shellGradient: string;
  sidebarBg: string;
};

/** Hardened dark — readable first, atmospheric second.
 *
 * These dark values mirror the `--aethos-*` tokens in `web/app/globals.css`
 * (the single source of truth). They stay as concrete hex/rgba (rather than
 * `var(--aethos-*)`) only because the theme provider and accessibility-mode
 * overrides compare/derive colors at runtime. When a token changes in
 * globals.css, update the matching value here too. */
export const darkOperationalPalette: McColorTokens = {
  bg: "#080b12",
  bgElevated: "#0e1018",
  bgCard: "#12141f",
  bgSurfacePrimary: "#12121c",
  bgSurfaceSolid: "#0e0e16",
  border: "rgba(255,255,255,0.10)",
  borderSubtle: "rgba(255,255,255,0.06)",
  text: "#e4e4e7",
  textStrong: "#ffffff",
  textMuted: "#a1a1aa",
  textDim: "#9ca3af",
  textNavInactive: "#b4b4c0",
  green: "#34d399",
  amber: "#fbbf24",
  red: "#f87171",
  cyan: "#22d3ee",
  navy: "#0e1424",
  // Deep-navy canvas with faint cyan (top-left) + violet (top-right) corner glows.
  shellGradient:
    "radial-gradient(1100px 560px at 12% -12%, rgba(34,211,238,0.07), transparent 60%)," +
    " radial-gradient(1000px 560px at 100% -8%, rgba(167,139,250,0.07), transparent 58%)," +
    " linear-gradient(160deg, #04060c 0%, #070a12 55%, #080b12 100%)",
  sidebarBg: "rgba(10,13,22,0.92)",
};

/** Calm light — Apple Notes × Linear operational clarity. */
export const lightOperationalPalette: McColorTokens = {
  bg: "#f2f3f5",
  bgElevated: "#ffffff",
  bgCard: "#ffffff",
  bgSurfacePrimary: "#ffffff",
  bgSurfaceSolid: "#fafafa",
  border: "rgba(15,23,42,0.14)",
  borderSubtle: "rgba(15,23,42,0.09)",
  text: "#0f0f12",
  textStrong: "#09090b",
  textMuted: "#3f3f46",
  textDim: "#52525b",
  textNavInactive: "#27272a",
  green: "#16a34a",
  amber: "#d97706",
  red: "#dc2626",
  cyan: "#0891b2",
  navy: "#e4e8ef",
  shellGradient: "linear-gradient(160deg, #f2f3f5 0%, #eef0f4 50%, #f2f3f5 100%)",
  sidebarBg: "rgba(255,255,255,0.98)",
};

export function resolveOperationalPalette(
  theme: McResolvedTheme,
  accessibility: McAccessibilityMode = "standard",
): McColorTokens {
  const base = theme === "light" ? lightOperationalPalette : darkOperationalPalette;
  if (accessibility === "high-readability" || accessibility === "focus") {
    return {
      ...base,
      textMuted: theme === "light" ? "#27272a" : "#d6d6de",
      textDim: theme === "light" ? "#3f3f46" : "#b8b8c4",
      textNavInactive: theme === "light" ? "#27272a" : "#cacad6",
      border: theme === "light" ? "rgba(15,23,42,0.20)" : "rgba(255,255,255,0.20)",
      borderSubtle: theme === "light" ? "rgba(15,23,42,0.14)" : "rgba(255,255,255,0.14)",
      bgCard: theme === "light" ? "#ffffff" : "#161622",
      bgSurfacePrimary: theme === "light" ? "#ffffff" : "#14141f",
    };
  }
  return base;
}

export function paletteToCssVars(palette: McColorTokens): Record<string, string> {
  return {
    "--mc-bg": palette.bg,
    "--mc-bg-elevated": palette.bgElevated,
    "--mc-bg-card": palette.bgCard,
    "--mc-surface-primary": palette.bgSurfacePrimary,
    "--mc-surface-solid": palette.bgSurfaceSolid,
    "--mc-border": palette.border,
    "--mc-border-subtle": palette.borderSubtle,
    "--mc-text": palette.text,
    "--mc-text-strong": palette.textStrong,
    "--mc-text-muted": palette.textMuted,
    "--mc-text-dim": palette.textDim,
    "--mc-text-nav-inactive": palette.textNavInactive,
    "--mc-green": palette.green,
    "--mc-amber": palette.amber,
    "--mc-red": palette.red,
    "--mc-cyan": palette.cyan,
    "--mc-shell-gradient": palette.shellGradient,
    "--mc-sidebar-bg": palette.sidebarBg,
  };
}
