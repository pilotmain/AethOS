/**
 * Browser mic capture via MediaRecorder for server-side Whisper transcription.
 * Used when VOICE_STT_PROVIDER=whisper; falls back to Web Speech API otherwise.
 */

export type RecorderHandle = {
  stop: () => Promise<Blob | null>;
  abort: () => void;
};

export function isMediaRecorderSupported(): boolean {
  return typeof window !== "undefined" && typeof MediaRecorder !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia);
}

export async function startMediaRecorderCapture(): Promise<RecorderHandle | null> {
  if (!isMediaRecorderSupported()) return null;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks: BlobPart[] = [];
    const recorder = new MediaRecorder(stream, { mimeType: preferredMimeType() });
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    };
    recorder.start();
    let stopped = false;
    return {
      stop: () =>
        new Promise((resolve) => {
          if (stopped) {
            resolve(null);
            return;
          }
          stopped = true;
          recorder.onstop = () => {
            stream.getTracks().forEach((track) => track.stop());
            resolve(chunks.length ? new Blob(chunks, { type: recorder.mimeType || "audio/webm" }) : null);
          };
          try {
            recorder.stop();
          } catch {
            stream.getTracks().forEach((track) => track.stop());
            resolve(null);
          }
        }),
      abort: () => {
        stopped = true;
        try {
          recorder.stop();
        } catch {
          /* noop */
        }
        stream.getTracks().forEach((track) => track.stop());
      },
    };
  } catch {
    return null;
  }
}

function preferredMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) return "audio/webm;codecs=opus";
  if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
  if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
  return undefined;
}
