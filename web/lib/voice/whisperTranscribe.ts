import { apiBase } from "@/lib/api";

/** Server-side Whisper transcription — audio never leaves except to our API. */
export async function transcribeAudioBlob(blob: Blob): Promise<string | null> {
  const form = new FormData();
  const ext = blob.type.includes("mp4") ? "m4a" : "webm";
  form.append("audio", blob, `capture.${ext}`);
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/voice/transcribe`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) return null;
    const body = (await res.json()) as { transcript?: string };
    return (body.transcript || "").trim() || null;
  } catch {
    return null;
  }
}
