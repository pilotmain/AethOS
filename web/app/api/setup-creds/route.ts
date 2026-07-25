/**
 * Legacy Nexa/bootstrap bridge — stale clients may call this on the Next dev server.
 * Clean AethOS uses NEXT_PUBLIC_API_BASE + /api/v1/health (not setup-creds).
 */
import { NextResponse } from "next/server";

const DEFAULT_API_BASE = "http://localhost:8010";

export async function GET() {
  const api_base = (process.env.NEXT_PUBLIC_API_BASE || DEFAULT_API_BASE).replace(/\/$/, "");
  return NextResponse.json({
    ok: true,
    deprecated: true,
    api_base,
    message: "Use /api/v1/health and /api/v1/runtime/status instead.",
  });
}
