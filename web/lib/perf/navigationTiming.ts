/** First-load and route-change timing — enabled when verbose/trace mode is on. */

const VERBOSE_KEY = "aethos_verbose_trace";

export function isVerboseTraceEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(VERBOSE_KEY) === "1" || localStorage.getItem(VERBOSE_KEY) === "true";
  } catch {
    return false;
  }
}

type NavMark = {
  label: string;
  at: number;
  detail?: string;
};

const marks: NavMark[] = [];

function pushMark(label: string, detail?: string) {
  if (!isVerboseTraceEnabled()) return;
  marks.push({ label, detail, at: performance.now() });
  if (marks.length > 40) marks.shift();
  const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
  const ttfb = nav ? Math.round(nav.responseStart - nav.requestStart) : null;
  const parts = [label, detail, ttfb != null ? `ttfb=${ttfb}ms` : null].filter(Boolean);
  console.info(`[aethos:nav] ${parts.join(" · ")}`);
}

export function markNavigation(label: string, detail?: string): void {
  pushMark(label, detail);
}

export function installNavigationTiming(): void {
  if (typeof window === "undefined" || !isVerboseTraceEnabled()) return;

  pushMark("boot");

  window.addEventListener("load", () => {
    const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    if (!nav) return;
    pushMark(
      "load",
      `dom=${Math.round(nav.domContentLoadedEventEnd - nav.startTime)}ms total=${Math.round(nav.loadEventEnd - nav.startTime)}ms`,
    );
  });

  const origPush = history.pushState.bind(history);
  history.pushState = (...args) => {
    pushMark("route-change", String(args[2] ?? ""));
    return origPush(...args);
  };
  const origReplace = history.replaceState.bind(history);
  history.replaceState = (...args) => {
    pushMark("route-replace", String(args[2] ?? ""));
    return origReplace(...args);
  };
}
