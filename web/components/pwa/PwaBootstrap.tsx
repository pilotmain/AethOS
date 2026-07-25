"use client";

import { useEffect } from "react";

import { installNavigationTiming } from "@/lib/perf/navigationTiming";
import { registerAethosServiceWorker } from "@/lib/pwa/registerServiceWorker";

/** Registers the offline shell service worker on first load. */
export function PwaBootstrap() {
  useEffect(() => {
    installNavigationTiming();
    void registerAethosServiceWorker();
  }, []);
  return null;
}
