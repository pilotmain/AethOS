"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchPwaStatus, subscribeWebPush, unsubscribeWebPush } from "@/lib/pwa/pwaApi";
import { registerAethosServiceWorker } from "@/lib/pwa/registerServiceWorker";
import { withBasePath } from "@/lib/pwa/basePath";

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const base64Safe = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64Safe);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i);
  return out;
}

export function useWebPush() {
  const [supported, setSupported] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ok =
      typeof window !== "undefined" &&
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window;
    setSupported(ok);
    if (!ok) return;
    void fetchPwaStatus().then((status) => setEnabled(Boolean(status?.web_push_enabled)));
  }, []);

  const subscribe = useCallback(async () => {
    setError(null);
    if (!supported) {
      setError("Push notifications are not supported in this browser.");
      return false;
    }
    const status = await fetchPwaStatus();
    if (!status?.web_push_enabled || !status.vapid_public_key) {
      setError("Web push is disabled on the server — set WEB_PUSH_ENABLED and VAPID keys.");
      return false;
    }
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      setError("Notification permission was denied.");
      return false;
    }
    const reg = await registerAethosServiceWorker();
    if (!reg) {
      setError("Could not register the offline shell service worker.");
      return false;
    }
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(status.vapid_public_key) as BufferSource,
    });
    const ok = await subscribeWebPush(sub);
    if (!ok) {
      setError("Failed to save push subscription.");
      return false;
    }
    setSubscribed(true);
    return true;
  }, [supported]);

  const unsubscribe = useCallback(async () => {
    setError(null);
    const reg = await navigator.serviceWorker.getRegistration(withBasePath("/"));
    const sub = await reg?.pushManager.getSubscription();
    if (sub) {
      await unsubscribeWebPush(sub.endpoint);
      await sub.unsubscribe();
    }
    setSubscribed(false);
    return true;
  }, []);

  return { supported, enabled, subscribed, error, subscribe, unsubscribe };
}
