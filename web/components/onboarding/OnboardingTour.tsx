"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useMissionControlTheme } from "@/lib/missionControl/theme";
import {
  TOUR_ANCHORS,
  buildWalkthroughSteps,
  hasSeenWalkthrough,
  markWalkthroughSeen,
  type WalkthroughStep,
} from "@/lib/onboarding/walkthrough";

type Props = {
  /** Per-user scope (email) so the "seen" flag never leaks across accounts. */
  scope: string;
  displayName?: string;
  /** When false, the tour stays dormant (e.g. on the login screen). */
  enabled?: boolean;
  /** Reports the anchor of the active step (or undefined when closed) so the host
   * can reveal a target that lives in a collapsed tray before the spotlight lands. */
  onActiveAnchorChange?: (anchor?: string) => void;
};

const CARD_WIDTH = 340;

type Rect = { top: number; left: number; width: number; height: number };

function anchorRect(anchor?: string): Rect | null {
  if (!anchor || typeof document === "undefined") return null;
  const el = document.querySelector(`[data-tour="${anchor}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return null;
  return { top: r.top, left: r.left, width: r.width, height: r.height };
}

function cardPosition(step: WalkthroughStep, rect: Rect | null): {
  position: "fixed";
  top?: number;
  left?: number;
  transform?: string;
} {
  if (!rect || !step.anchor || step.placement === "center") {
    return { position: "fixed", top: "50%" as unknown as number, left: "50%" as unknown as number, transform: "translate(-50%, -50%)" };
  }
  const vw = typeof window !== "undefined" ? window.innerWidth : 1280;
  const vh = typeof window !== "undefined" ? window.innerHeight : 800;
  const clampLeft = (l: number) => Math.max(12, Math.min(l, vw - CARD_WIDTH - 12));
  const clampTop = (t: number) => Math.max(12, Math.min(t, vh - 220));
  switch (step.placement) {
    case "right":
      return { position: "fixed", top: clampTop(rect.top), left: clampLeft(rect.left + rect.width + 14) };
    case "left":
      return { position: "fixed", top: clampTop(rect.top), left: clampLeft(rect.left - CARD_WIDTH - 14) };
    case "bottom":
    default:
      return { position: "fixed", top: clampTop(rect.top + rect.height + 14), left: clampLeft(rect.left) };
  }
}

export function OnboardingTour({ scope, displayName, enabled = true, onActiveAnchorChange }: Props) {
  const { colors } = useMissionControlTheme();
  const steps = useMemo(() => buildWalkthroughSteps(displayName), [displayName]);

  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);

  const step = steps[index];

  // Auto-open once per user on first visit (after layout settles).
  useEffect(() => {
    if (!enabled) return;
    if (hasSeenWalkthrough(scope)) return;
    const t = setTimeout(() => {
      setIndex(0);
      setOpen(true);
    }, 650);
    return () => clearTimeout(t);
  }, [enabled, scope]);

  // Let the host reveal a target hidden in a collapsed tray before we measure it.
  useEffect(() => {
    onActiveAnchorChange?.(open ? step?.anchor : undefined);
  }, [open, step?.anchor, onActiveAnchorChange]);

  // Track the spotlight target as the step changes / the window moves. Re-measure a
  // couple of times so a just-revealed element (e.g. the Advanced tray expanding) is
  // caught rather than measured as missing.
  useEffect(() => {
    if (!open) return;
    const update = () => setRect(anchorRect(step?.anchor));
    update();
    const raf = requestAnimationFrame(update);
    const t1 = setTimeout(update, 80);
    const t2 = setTimeout(update, 220);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, step?.anchor]);

  const finish = useCallback(() => {
    markWalkthroughSeen(scope);
    setOpen(false);
  }, [scope]);

  const next = useCallback(() => {
    setIndex((i) => {
      if (i >= steps.length - 1) {
        markWalkthroughSeen(scope);
        setOpen(false);
        return i;
      }
      return i + 1;
    });
  }, [steps.length, scope]);

  const back = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);

  useEffect(() => {
    if (!open) return;
    cardRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish();
      else if (e.key === "ArrowRight" || e.key === "Enter") next();
      else if (e.key === "ArrowLeft") back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, finish, next, back]);

  const launcher = enabled ? (
    <button
      type="button"
      data-tour={TOUR_ANCHORS.launcher}
      onClick={() => {
        setIndex(0);
        setOpen(true);
      }}
      aria-label="Take the AethOS tour"
      title="Take the AethOS tour"
      style={{
        position: "fixed",
        bottom: 18,
        right: 18,
        zIndex: 3900,
        width: 38,
        height: 38,
        borderRadius: "50%",
        border: `1px solid ${colors.border}`,
        background: colors.bgCard,
        color: colors.cyan,
        fontSize: 18,
        fontWeight: 700,
        cursor: "pointer",
        boxShadow: "0 4px 14px rgba(0,0,0,0.28)",
        display: open ? "none" : "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      ?
    </button>
  ) : null;

  if (!open || !step) return launcher;

  const pos = cardPosition(step, rect);
  const isLast = index === steps.length - 1;

  return (
    <>
      {launcher}
      <div
        role="presentation"
        onClick={finish}
        style={{ position: "fixed", inset: 0, zIndex: 4000, background: rect ? "transparent" : "rgba(2,6,16,0.62)" }}
      >
        {/* Spotlight cut-out: a transparent box over the anchor, the rest dimmed via box-shadow. */}
        {rect ? (
          <div
            style={{
              position: "fixed",
              top: rect.top - 6,
              left: rect.left - 6,
              width: rect.width + 12,
              height: rect.height + 12,
              borderRadius: 12,
              boxShadow: "0 0 0 9999px rgba(2,6,16,0.62)",
              outline: `2px solid ${colors.cyan}`,
              pointerEvents: "none",
              transition: "all 0.18s ease",
            }}
          />
        ) : null}
      </div>

      <div
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-label={step.title}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        style={{
          ...pos,
          zIndex: 4001,
          width: CARD_WIDTH,
          maxWidth: "calc(100vw - 24px)",
          background: colors.bgCard,
          color: colors.text,
          border: `1px solid ${colors.border}`,
          borderRadius: 14,
          padding: 18,
          boxShadow: "0 16px 48px rgba(0,0,0,0.4)",
          outline: "none",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <span style={{ fontSize: 11, color: colors.textMuted, fontWeight: 600, letterSpacing: "0.04em" }}>
            Step {index + 1} of {steps.length}
          </span>
          <button
            type="button"
            onClick={finish}
            aria-label="Skip the tour"
            style={{ border: "none", background: "transparent", color: colors.textMuted, fontSize: 12, cursor: "pointer" }}
          >
            Skip
          </button>
        </div>

        <h2 style={{ margin: "0 0 8px", fontSize: 17, fontWeight: 650 }}>{step.title}</h2>
        <p style={{ margin: "0 0 16px", fontSize: 13.5, lineHeight: 1.55, color: colors.textMuted }}>{step.body}</p>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
          <div style={{ display: "flex", gap: 6 }}>
            {steps.map((s, i) => (
              <span
                key={s.id}
                aria-hidden
                style={{
                  width: i === index ? 16 : 6,
                  height: 6,
                  borderRadius: 3,
                  background: i === index ? colors.cyan : colors.border,
                  transition: "width 0.18s ease",
                }}
              />
            ))}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {index > 0 ? (
              <button
                type="button"
                onClick={back}
                style={{
                  padding: "7px 12px",
                  borderRadius: 9,
                  border: `1px solid ${colors.border}`,
                  background: "transparent",
                  color: colors.text,
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                Back
              </button>
            ) : null}
            <button
              type="button"
              onClick={next}
              style={{
                padding: "7px 14px",
                borderRadius: 9,
                border: "none",
                background: colors.cyan,
                color: "#04121b",
                fontSize: 13,
                fontWeight: 650,
                cursor: "pointer",
              }}
            >
              {isLast ? "Done" : index === 0 ? "Show me" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
