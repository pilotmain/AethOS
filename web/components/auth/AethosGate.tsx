"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";

import { AethosLoadingScreen } from "@/components/auth/AethosLoadingScreen";
import { AuthScopeProvider } from "@/lib/auth/AuthScopeContext";
import { TenantAuthCard } from "@/components/auth/TenantAuthCard";
import { TenantSetupWizard } from "@/components/auth/TenantSetupWizard";
import {
  fetchPersonaState,
  readOperatorToken,
  saveOperatorPersona,
  submitOperatorLogin,
  writeOperatorToken,
  type OperatorPersona,
  type PersonaState,
} from "@/lib/onboarding/persona";
import {
  fetchAuthSession,
  fetchTenantOnboarding,
  type AuthSessionState,
} from "@/lib/onboarding/tenantSetup";

type Phase = "loading" | "tenant-auth" | "tenant-setup" | "login" | "onboarding" | "ready";

const cardShell: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 24,
  background: "var(--aethos-bg-deep)",
  color: "var(--aethos-text)",
};

const card: React.CSSProperties = {
  width: "100%",
  maxWidth: 460,
  background: "var(--aethos-surface-strong)",
  border: "1px solid var(--aethos-border)",
  borderRadius: 16,
  padding: "28px 26px",
  boxShadow: "0 24px 64px rgba(0,0,0,0.4)",
};

const fieldLabel: React.CSSProperties = {
  display: "block",
  fontSize: 12,
  fontWeight: 600,
  color: "var(--aethos-text-muted)",
  marginBottom: 6,
  marginTop: 14,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  padding: "9px 11px",
  borderRadius: 10,
  border: "1px solid var(--aethos-border)",
  background: "var(--aethos-surface)",
  color: "var(--aethos-text)",
  fontSize: 14,
  outline: "none",
};

const primaryBtn: React.CSSProperties = {
  width: "100%",
  marginTop: 22,
  padding: "11px 14px",
  borderRadius: 10,
  border: "none",
  background: "var(--aethos-accent)",
  color: "var(--aethos-bg)",
  fontSize: 14,
  fontWeight: 700,
  cursor: "pointer",
};

const TONES: { id: string; label: string }[] = [
  { id: "warm", label: "Warm" },
  { id: "concise", label: "Concise" },
  { id: "direct", label: "Direct" },
  { id: "playful", label: "Playful" },
];

function Brand() {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.18em", fontWeight: 700, color: "var(--aethos-text-dim)" }}>
        AETHOS
      </div>
    </div>
  );
}

function LoginCard({ onAuthed }: { onAuthed: () => void }) {
  const [passphrase, setPassphrase] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = useCallback(async () => {
    setBusy(true);
    setError("");
    const res = await submitOperatorLogin(passphrase);
    setBusy(false);
    if (res.ok && res.token) {
      writeOperatorToken(res.token);
      onAuthed();
    } else {
      setError(res.error === "invalid_passphrase" ? "That passphrase didn't match. Try again." : "Couldn't sign in. Check the server and retry.");
    }
  }, [passphrase, onAuthed]);

  return (
    <div style={cardShell}>
      <div style={card}>
        <Brand />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "2px 0 4px" }}>Welcome back</h1>
        <p style={{ fontSize: 13, color: "var(--aethos-text-muted)", margin: 0 }}>
          Sign in to your AethOS control plane.
        </p>
        <label style={fieldLabel} htmlFor="aethos-pass">Passphrase</label>
        <input
          id="aethos-pass"
          type="password"
          autoFocus
          value={passphrase}
          style={inputStyle}
          onChange={(e) => setPassphrase(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void submit();
          }}
        />
        {error ? <div style={{ color: "var(--aethos-danger)", fontSize: 12, marginTop: 10 }}>{error}</div> : null}
        <button type="button" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }} disabled={busy} onClick={() => void submit()}>
          {busy ? "Signing in…" : "Enter AethOS"}
        </button>
      </div>
    </div>
  );
}

function OnboardingCard({ persona, onDone }: { persona: OperatorPersona; onDone: () => void }) {
  const guessTz = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    } catch {
      return "";
    }
  }, []);

  const [name, setName] = useState(persona.name || "");
  const [timezone, setTimezone] = useState(persona.timezone || guessTz);
  const [startHour, setStartHour] = useState<number>(persona.work_start_hour ?? 9);
  const [endHour, setEndHour] = useState<number>(persona.work_end_hour ?? 18);
  const [tone, setTone] = useState(persona.tone || "warm");
  const [goals, setGoals] = useState((persona.goals || []).join("\n"));
  const [busy, setBusy] = useState(false);

  const submit = useCallback(async () => {
    setBusy(true);
    await saveOperatorPersona({
      name: name.trim(),
      timezone: timezone.trim(),
      work_start_hour: startHour,
      work_end_hour: endHour,
      tone,
      goals: goals
        .split("\n")
        .map((g) => g.trim())
        .filter(Boolean),
      first_run_complete: true,
    });
    setBusy(false);
    onDone();
  }, [name, timezone, startHour, endHour, tone, goals, onDone]);

  const hourOptions = Array.from({ length: 24 }, (_, h) => h);

  return (
    <div style={cardShell}>
      <div style={{ ...card, maxWidth: 520 }}>
        <Brand />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "2px 0 4px" }}>Let&apos;s get acquainted</h1>
        <p style={{ fontSize: 13, color: "var(--aethos-text-muted)", margin: "0 0 12px" }}>
          I can govern deployments, debug failures with evidence, run multi-model arbiter sessions, review PRs and CI
          health, and execute governed mutations with your approval — plus inspect infrastructure across Railway,
          Vercel, and GitHub once you connect them.
        </p>
        <p style={{ fontSize: 13, color: "var(--aethos-text-muted)", margin: 0 }}>
          A few quick things about you so I can match your hours and tone. You can change these anytime.
        </p>

        <label style={fieldLabel} htmlFor="ob-name">What should I call you?</label>
        <input id="ob-name" autoFocus value={name} style={inputStyle} onChange={(e) => setName(e.target.value)} placeholder="Your name" />

        <label style={fieldLabel} htmlFor="ob-tz">Your timezone</label>
        <input id="ob-tz" value={timezone} style={inputStyle} onChange={(e) => setTimezone(e.target.value)} placeholder="e.g. America/New_York" />

        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={fieldLabel} htmlFor="ob-start">Working hours — start</label>
            <select id="ob-start" value={startHour} style={inputStyle} onChange={(e) => setStartHour(Number(e.target.value))}>
              {hourOptions.map((h) => (
                <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label style={fieldLabel} htmlFor="ob-end">end</label>
            <select id="ob-end" value={endHour} style={inputStyle} onChange={(e) => setEndHour(Number(e.target.value))}>
              {hourOptions.map((h) => (
                <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
              ))}
            </select>
          </div>
        </div>

        <label style={fieldLabel}>Preferred tone</label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {TONES.map((t) => {
            const active = tone === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTone(t.id)}
                style={{
                  padding: "7px 14px",
                  borderRadius: 999,
                  border: `1px solid ${active ? "var(--aethos-accent)" : "var(--aethos-border)"}`,
                  background: active ? "var(--aethos-accent-soft)" : "transparent",
                  color: active ? "var(--aethos-accent)" : "var(--aethos-text-muted)",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        <label style={fieldLabel} htmlFor="ob-goals">What are you hoping to do with AethOS? (one per line)</label>
        <textarea
          id="ob-goals"
          value={goals}
          style={{ ...inputStyle, minHeight: 76, resize: "vertical", fontFamily: "inherit" }}
          onChange={(e) => setGoals(e.target.value)}
          placeholder={"Ship and operate my services\nKeep an eye on deployments"}
        />

        <button type="button" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }} disabled={busy} onClick={() => void submit()}>
          {busy ? "Saving…" : name.trim() ? `Start, ${name.trim().split(" ")[0]}` : "Start"}
        </button>
        <button
          type="button"
          onClick={() => void submit()}
          style={{
            width: "100%",
            marginTop: 10,
            padding: "6px",
            border: "none",
            background: "transparent",
            color: "var(--aethos-text-dim)",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          Skip for now
        </button>
      </div>
    </div>
  );
}

export function AethosGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [phase, setPhase] = useState<Phase>("loading");
  const [state, setState] = useState<PersonaState | null>(null);
  const [authSession, setAuthSession] = useState<AuthSessionState | null>(null);

  if (pathname?.includes("/verify-email")) {
    return <>{children}</>;
  }

  const evaluatePersona = useCallback((s: PersonaState | null) => {
    if (!s || !s.ok) {
      setPhase("ready");
      return;
    }
    setState(s);
    if (s.login_required && !readOperatorToken()) {
      setPhase("login");
      return;
    }
    if (s.onboarding_enabled && s.first_run) {
      setPhase("onboarding");
      return;
    }
    setPhase("ready");
  }, []);

  const evaluateMultiTenant = useCallback(async (session: AuthSessionState | null) => {
    if (!session?.multi_tenant_enabled) {
      return false;
    }
    setAuthSession(session);
    if (!session.authenticated) {
      setPhase("tenant-auth");
      return true;
    }
    const onboarding = await fetchTenantOnboarding();
    if (onboarding?.required || !onboarding) {
      // null onboarding usually means the session cookie didn't reach the API
      // (CORS/credentials on localhost) — show BYOK setup instead of skipping it.
      setPhase("tenant-setup");
      return true;
    }
    setPhase("ready");
    return true;
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const sessionPromise = fetchAuthSession();
      const personaPromise = fetchPersonaState();
      const session = await sessionPromise;
      if (cancelled) return;
      const mt = await evaluateMultiTenant(session);
      if (mt) return;
      const s = await personaPromise;
      if (!cancelled) evaluatePersona(s);
    })();
    return () => {
      cancelled = true;
    };
  }, [evaluatePersona, evaluateMultiTenant]);

  if (phase === "loading") {
    return <AethosLoadingScreen />;
  }

  if (phase === "tenant-auth") {
    return (
      <TenantAuthCard
        selfSignupEnabled={Boolean(authSession?.self_signup_enabled)}
        onAuthed={() => {
          void (async () => {
            const session = await fetchAuthSession();
            if (session) setAuthSession(session);
            const onboarding = await fetchTenantOnboarding();
            if (onboarding?.required || !onboarding) setPhase("tenant-setup");
            else setPhase("ready");
          })();
        }}
      />
    );
  }

  if (phase === "tenant-setup") {
    return (
      <TenantSetupWizard
        onDone={() => {
          void fetchPersonaState().then((s) => {
            if (s?.onboarding_enabled && s.first_run) setPhase("onboarding");
            else setPhase("ready");
          });
        }}
      />
    );
  }

  if (phase === "login") {
    return (
      <LoginCard
        onAuthed={() => {
          if (state?.onboarding_enabled && state.first_run) setPhase("onboarding");
          else setPhase("ready");
        }}
      />
    );
  }

  if (phase === "onboarding") {
    return (
      <OnboardingCard
        persona={state?.persona ?? ({
          name: "",
          timezone: "",
          work_start_hour: null,
          work_end_hour: null,
          tone: "warm",
          goals: [],
          first_run_complete: false,
          updated_at: null,
        } as OperatorPersona)}
        onDone={() => setPhase("ready")}
      />
    );
  }

  return <AuthScopeProvider>{children}</AuthScopeProvider>;
}
