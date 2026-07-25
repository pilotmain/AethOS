"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  paletteToCssVars,
  resolveOperationalPalette,
  type McAccessibilityMode,
  type McColorTokens,
  type McResolvedTheme,
  type McThemePreference,
} from "@/lib/missionControl/theme/operationalPalette";
import {
  loadAccessibilityMode,
  loadThemePreference,
  prefersReducedMotion,
  resolveSystemTheme,
  saveAccessibilityMode,
  saveThemePreference,
} from "@/lib/missionControl/theme/themeState";

type MissionControlThemeContextValue = {
  themePreference: McThemePreference;
  resolvedTheme: McResolvedTheme;
  accessibilityMode: McAccessibilityMode;
  colors: McColorTokens;
  cssVars: Record<string, string>;
  reducedMotion: boolean;
  setThemePreference: (theme: McThemePreference) => void;
  setAccessibilityMode: (mode: McAccessibilityMode) => void;
};

const MissionControlThemeContext = createContext<MissionControlThemeContextValue | null>(null);

export function MissionControlThemeProvider({ children }: { children: ReactNode }) {
  const [themePreference, setThemePreferenceState] = useState<McThemePreference>("dark");
  const [accessibilityMode, setAccessibilityModeState] = useState<McAccessibilityMode>("standard");
  const [systemTheme, setSystemTheme] = useState<McResolvedTheme>("dark");
  const [reducedMotion, setReducedMotion] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setThemePreferenceState(loadThemePreference());
    setAccessibilityModeState(loadAccessibilityMode());
    setSystemTheme(resolveSystemTheme());
    setReducedMotion(prefersReducedMotion());
    setHydrated(true);

    const media = window.matchMedia("(prefers-color-scheme: light)");
    const onScheme = () => setSystemTheme(media.matches ? "light" : "dark");
    media.addEventListener("change", onScheme);

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onMotion = () => setReducedMotion(motion.matches);
    motion.addEventListener("change", onMotion);

    return () => {
      media.removeEventListener("change", onScheme);
      motion.removeEventListener("change", onMotion);
    };
  }, []);

  const resolvedTheme: McResolvedTheme =
    themePreference === "system" ? systemTheme : themePreference;

  const colors = useMemo(
    () => resolveOperationalPalette(resolvedTheme, accessibilityMode),
    [resolvedTheme, accessibilityMode],
  );

  const cssVars = useMemo(() => paletteToCssVars(colors), [colors]);

  useEffect(() => {
    if (!hydrated) return;
    const root = document.documentElement;
    root.dataset.mcTheme = resolvedTheme;
    root.dataset.mcA11y = accessibilityMode;
    root.dataset.mcGrounding = "operational";
    root.dataset.mcSignal = "hierarchy";
    root.dataset.mcReducedMotion = reducedMotion ? "true" : undefined;
    root.style.colorScheme = resolvedTheme;
    Object.entries(cssVars).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });
  }, [hydrated, resolvedTheme, accessibilityMode, reducedMotion, cssVars]);

  const setThemePreference = useCallback((theme: McThemePreference) => {
    setThemePreferenceState(theme);
    saveThemePreference(theme);
  }, []);

  const setAccessibilityMode = useCallback((mode: McAccessibilityMode) => {
    setAccessibilityModeState(mode);
    saveAccessibilityMode(mode);
  }, []);

  const value = useMemo(
    () => ({
      themePreference,
      resolvedTheme,
      accessibilityMode,
      colors,
      cssVars,
      reducedMotion,
      setThemePreference,
      setAccessibilityMode,
    }),
    [
      themePreference,
      resolvedTheme,
      accessibilityMode,
      colors,
      cssVars,
      reducedMotion,
      setThemePreference,
      setAccessibilityMode,
    ],
  );

  return (
    <MissionControlThemeContext.Provider value={value}>{children}</MissionControlThemeContext.Provider>
  );
}

export function useMissionControlTheme(): MissionControlThemeContextValue {
  const ctx = useContext(MissionControlThemeContext);
  if (!ctx) {
    throw new Error("useMissionControlTheme must be used within MissionControlThemeProvider");
  }
  return ctx;
}
