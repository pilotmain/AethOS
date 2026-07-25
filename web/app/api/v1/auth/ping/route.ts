/** Legacy auth probe — compatibility shim for stale web bundles. */
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ ok: true, deprecated: true });
}
