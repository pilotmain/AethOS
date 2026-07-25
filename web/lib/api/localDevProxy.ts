/** Dev-only reverse proxy to the FastAPI backend (forwards session cookies). */

import { type NextRequest } from "next/server";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

export function localDevApiOrigin(): string {
  const port = process.env.AETHOS_API_PORT || "8010";
  const fromEnv = process.env.AETHOS_API_ORIGIN?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return `http://127.0.0.1:${port}`;
}

export function shouldUseLocalDevApiProxy(): boolean {
  return process.env.NODE_ENV !== "production";
}

function forwardHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (HOP_BY_HOP.has(lower) || lower === "host") return;
    headers.set(key, value);
  });
  return headers;
}

function responseHeaders(upstream: Response): Headers {
  const headers = new Headers();
  upstream.headers.forEach((value, key) => {
    if (HOP_BY_HOP.has(key.toLowerCase())) return;
    headers.set(key, value);
  });
  return headers;
}

export async function proxyToLocalApi(request: NextRequest, pathSegments: string[]): Promise<Response> {
  const encodedPath = pathSegments.map((segment) => encodeURIComponent(segment)).join("/");
  const target = `${localDevApiOrigin()}/api/v1/${encodedPath}${request.nextUrl.search}`;
  const method = request.method.toUpperCase();
  const headers = forwardHeaders(request);
  const hasBody = method !== "GET" && method !== "HEAD";
  const body = hasBody ? await request.arrayBuffer() : undefined;

  const upstream = await fetch(target, {
    method,
    headers,
    body: body && body.byteLength > 0 ? body : undefined,
    redirect: "manual",
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders(upstream),
  });
}
