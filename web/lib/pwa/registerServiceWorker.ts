import { CLIENT_APP_VERSION } from "@/lib/pwa/appVersion";
import { publicBasePath, withBasePath } from "@/lib/pwa/basePath";

export async function registerAethosServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return null;
  try {
    const swUrl = `${withBasePath("/sw.js")}?build=${encodeURIComponent(CLIENT_APP_VERSION)}`;
    const reg = await navigator.serviceWorker.register(swUrl, {
      scope: `${publicBasePath() || ""}/`,
    });
    return reg;
  } catch {
    return null;
  }
}
