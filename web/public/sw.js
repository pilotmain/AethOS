/* AethOS offline shell + web push (§4 PWA). */
// Cache name includes build id from registration URL (?build=…) or falls back below.
const BUILD =
  typeof URL !== "undefined"
    ? new URL(self.location.href).searchParams.get("build") || "v0"
    : "v0";
const CACHE = `aethos-shell-${BUILD}`;

function basePath() {
  const path = self.location.pathname || "/";
  return path.endsWith("/sw.js") ? path.slice(0, -"/sw.js".length) : "";
}

function shellUrls() {
  const base = basePath();
  const root = base || "/";
  return [root, `${base}/manifest.webmanifest`];
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(shellUrls()).catch(() => undefined)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    fetch(event.request).catch(() =>
      caches.match(event.request).then((cached) => cached || caches.match(shellUrls()[0])),
    ),
  );
});

self.addEventListener("push", (event) => {
  let payload = { title: "AethOS", body: "", url: "/" };
  try {
    if (event.data) payload = { ...payload, ...event.data.json() };
  } catch {
    payload.body = event.data ? String(event.data.text()) : "";
  }
  const base = basePath();
  const target = payload.url && payload.url.startsWith("/") ? `${base}${payload.url}` : payload.url || base || "/";
  event.waitUntil(
    self.registration.showNotification(payload.title || "AethOS", {
      body: payload.body || "",
      icon: `${base}/icons/icon.svg`,
      badge: `${base}/icons/icon.svg`,
      tag: payload.tag || "aethos",
      data: { url: target },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || basePath() || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client && client.url.includes(url)) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
      return undefined;
    }),
  );
});
