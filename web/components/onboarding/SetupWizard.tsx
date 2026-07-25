"use client";

import { useState } from "react";

const STEPS = ["persona", "model", "connections", "try_it"] as const;

export function SetupWizard({ onComplete }: { onComplete?: () => void }) {
  const [step, setStep] = useState(0);
  const [skipped, setSkipped] = useState<Record<string, boolean>>({});

  const current = STEPS[step] ?? "persona";

  function skip() {
    setSkipped((s) => ({ ...s, [current]: true }));
    if (step >= STEPS.length - 1) {
      onComplete?.();
      return;
    }
    setStep((n) => Math.min(n + 1, STEPS.length - 1));
  }

  function next() {
    if (step >= STEPS.length - 1) {
      onComplete?.();
      return;
    }
    setStep((n) => n + 1);
  }

  return (
    <div className="aethos-setup-wizard" data-step={current}>
      <header>
        <h2>AethOS setup</h2>
        <p>Step {step + 1} of {STEPS.length} — every step is skippable.</p>
      </header>
      {current === "persona" && <p>Tell AethOS your name, timezone, and tone.</p>}
      {current === "model" && <p>Pick a cloud model key or serve one locally in Foundry.</p>}
      {current === "connections" && <p>Connect providers from the registry-driven catalog.</p>}
      {current === "try_it" && <p>Ask a question in chat — you are ready.</p>}
      <div className="aethos-setup-actions">
        <button type="button" onClick={skip}>Skip</button>
        <button type="button" onClick={next}>Continue</button>
      </div>
      {Object.keys(skipped).length > 0 && (
        <p className="aethos-text-muted">Skipped: {Object.keys(skipped).join(", ")}</p>
      )}
    </div>
  );
}
