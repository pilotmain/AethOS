"use client";

import {
  mcButtonPrimaryStyle,
  mcColors,
  mcInputStyle,
} from "@/lib/missionControl/layout";
import { chatComposerDockStyle } from "@/lib/chat/layout";
import type { ModelCatalogEntry } from "@/lib/chat/modelSelection";
import { ChatVoiceControls } from "@/components/chat/ChatVoiceControls";
import type { VoiceController } from "@/lib/voice/useVoice";

export type ChatInteractionMode = "agent" | "chat";

export type QueuedInputKind = "steering" | "follow_up";
export type QueuedInput = { id: string; text: string; kind: QueuedInputKind };

type Props = {
  input: string;
  sending: boolean;
  mode: ChatInteractionMode;
  onModeChange: (mode: ChatInteractionMode) => void;
  modelCatalogId: string;
  modelOptions: ModelCatalogEntry[];
  modelLoading?: boolean;
  onModelChange: (catalogId: string) => void;
  onChange: (value: string) => void;
  onSend: () => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  queued?: QueuedInput[];
  onQueue?: (text: string, kind: QueuedInputKind) => void;
  onDequeue?: (id: string) => void;
  onStop?: () => void;
  voice?: VoiceController;
};

export function ChatComposer({
  input,
  sending,
  mode,
  onModeChange,
  modelCatalogId,
  modelOptions,
  modelLoading,
  onModelChange,
  onChange,
  onSend,
  inputRef,
  queued = [],
  onQueue,
  onDequeue,
  onStop,
  voice,
}: Props) {
  return (
    <footer style={chatComposerDockStyle}>
      {voice ? <ChatVoiceControls voice={voice} busy={sending} /> : null}
      {queued.length > 0 ? (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
            maxWidth: 1100,
            margin: "0 auto 8px",
            width: "100%",
          }}
        >
          <span style={{ fontSize: 11, color: mcColors.textDim, alignSelf: "center" }}>
            Queued while agent runs:
          </span>
          {queued.map((q) => (
            <button
              key={q.id}
              type="button"
              onClick={() => onDequeue?.(q.id)}
              title="Click to pull this back into the editor"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 10px",
                borderRadius: 999,
                fontSize: 11,
                cursor: "pointer",
                border: `1px solid ${q.kind === "steering" ? mcColors.cyan : mcColors.borderSubtle}`,
                background: q.kind === "steering" ? "rgba(34,211,238,0.12)" : "rgba(255,255,255,0.03)",
                color: mcColors.textMuted,
              }}
            >
              <span style={{ fontWeight: 700, color: q.kind === "steering" ? mcColors.cyan : mcColors.textDim }}>
                {q.kind === "steering" ? "steer" : "next"}
              </span>
              {q.text.length > 40 ? `${q.text.slice(0, 40)}…` : q.text}
              <span style={{ color: mcColors.textDim }}>×</span>
            </button>
          ))}
        </div>
      ) : null}
      <div
        style={{
          display: "flex",
          gap: 12,
          alignItems: "flex-end",
          // Fill the available width — the text box expands; controls stay a fixed size.
          width: "100%",
        }}
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key !== "Enter") return;
            // While the agent is working, Enter queues a steering note (applied
            // next), Alt/Shift+Enter queues a follow-up (after all work). §5
            if (sending && onQueue) {
              const text = input.trim();
              if (!text) {
                e.preventDefault();
                return;
              }
              e.preventDefault();
              onQueue(text, e.altKey || e.shiftKey ? "follow_up" : "steering");
              onChange("");
              return;
            }
            if (!e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          rows={3}
          placeholder={
            sending
              ? "Agent is working — Enter queues a steering note, Alt/Shift+Enter a follow-up…"
              : mode === "agent"
                ? "Ask AethOS to research, orchestrate agents, or inspect providers…"
                : "Conversational message — tools run only when you ask explicitly…"
          }
          className="chat-composer-input"
          style={{
            ...mcInputStyle,
            flex: 1,
            minHeight: 72,
            maxHeight: 200,
            resize: "vertical",
            padding: "14px 16px",
            fontSize: 14,
            lineHeight: 1.5,
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
          }}
        />
        <div style={{ display: "flex", flexDirection: "column", gap: 8, alignSelf: "stretch", width: 180, flexShrink: 0 }}>
          <div
            style={{
              display: "flex",
              borderRadius: 999,
              border: `1px solid ${mcColors.borderSubtle}`,
              overflow: "hidden",
              fontSize: 11,
              fontWeight: 600,
            }}
          >
            {(["agent", "chat"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => onModeChange(m)}
                style={{
                  border: "none",
                  padding: "6px 12px",
                  cursor: "pointer",
                  textTransform: "capitalize",
                  background: mode === m ? "rgba(34,211,238,0.18)" : "transparent",
                  color: mode === m ? mcColors.cyan : mcColors.textMuted,
                }}
              >
                {m}
              </button>
            ))}
          </div>
          {mode === "agent" ? (
            <select
              value={modelCatalogId}
              disabled={sending || modelLoading || modelOptions.length === 0}
              onChange={(e) => onModelChange(e.target.value)}
              aria-label="Agent model"
              style={{
                ...mcInputStyle,
                padding: "8px 10px",
                fontSize: 11,
                fontWeight: 600,
                cursor: "pointer",
                width: "100%",
                maxWidth: "100%",
              }}
            >
              {modelOptions.map((opt) => {
                const toolCapable = opt.agent_tool_capable !== false;
                return (
                  <option
                    key={opt.id}
                    value={opt.id}
                    disabled={!toolCapable}
                    title={toolCapable ? undefined : "tools require a cloud model in this build"}
                  >
                    {toolCapable ? opt.label : `${opt.label} (chat only)`}
                  </option>
                );
              })}
            </select>
          ) : null}
          {sending && onStop ? (
            <button
              type="button"
              onClick={onStop}
              style={{
                ...mcButtonPrimaryStyle,
                padding: "14px 22px",
                minHeight: 48,
                flex: 1,
                background: "rgba(248,113,113,0.16)",
                color: mcColors.red,
                border: `1px solid ${mcColors.red}`,
              }}
            >
              Stop
            </button>
          ) : (
            <button
              type="button"
              onClick={onSend}
              disabled={sending || !input.trim()}
              style={{
                ...mcButtonPrimaryStyle,
                padding: "14px 22px",
                minHeight: 48,
                flex: 1,
              }}
            >
              {sending ? "Running…" : "Send"}
            </button>
          )}
        </div>
      </div>
      <p style={{ margin: "10px 0 0", fontSize: 11, color: mcColors.textDim }}>
        Shift+Enter newline · Enter send · while running: Enter steers, Alt/Shift+Enter queues follow-up
        {mode === "agent" ? " · Ctrl/Cmd+M switch model" : ""} · Ctrl+B sidebar · Ctrl+J panel
      </p>
    </footer>
  );
}
