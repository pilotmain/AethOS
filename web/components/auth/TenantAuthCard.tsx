"use client";

import { useCallback, useState } from "react";

import { completeLoginClientState } from "@/lib/auth/AuthScopeContext";
import {
  loginWithPassword,
  registerAccount,
  resendVerificationEmail,
} from "@/lib/onboarding/tenantSetup";

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

type Props = {
  selfSignupEnabled: boolean;
  onAuthed: () => void;
};

export function TenantAuthCard({ selfSignupEnabled, onAuthed }: Props) {
  // Default to the login view even when self-signup is enabled — returning users
  // (and the demo recorder) land on Sign in first; new users tap "Need an account?".
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingVerification, setPendingVerification] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(false);
  const [resendMsg, setResendMsg] = useState("");

  const submit = useCallback(async () => {
    setBusy(true);
    setError("");
    setResendMsg("");
    const res =
      mode === "register"
        ? await registerAccount(email.trim(), password, name.trim())
        : await loginWithPassword(email.trim(), password);
    setBusy(false);
    if (res.ok && mode === "register" && (res as { pending?: boolean }).pending) {
      // Re-registration after a revoked/ended account: verify (if required) then it
      // waits for owner approval — do NOT sign them in.
      setPendingApproval(true);
      if (res.verification_required) setPendingVerification(true);
      return;
    }
    if (res.ok && mode === "register" && res.verification_required) {
      setPendingVerification(true);
      return;
    }
    if (res.ok) {
      await completeLoginClientState();
      onAuthed();
    } else {
      const msg =
        res.error === "invalid_credentials"
          ? "Email or password didn't match."
          : res.error === "email_verification_required"
            ? "Verify your email before signing in. Check your inbox for the confirmation link."
            : res.error === "access_pending"
              ? "Your account is awaiting approval. You'll be able to sign in once access is granted."
              : res.error === "access_revoked"
                ? "Your access has ended. Re-register with this email to request access again."
                : res.error === "access_expired"
                  ? "Your access has expired. Re-register with this email to request access again."
                  : res.error === "access_suspended"
                    ? "Your account is suspended. Contact the team if you think this is a mistake."
                    : res.error === "email_taken"
              ? "That email is already registered — try signing in."
              : res.error === "weak_password"
                ? res.detail || "Password must be at least 12 characters with letters and numbers."
                : res.error === "mailer_not_configured"
                  ? res.detail || "Email is not configured on this server. Contact the operator."
                  : res.error === "verification_email_failed"
                    ? [
                        res.detail,
                        "hint" in res ? res.hint : undefined,
                      ]
                        .filter(Boolean)
                        .join(" — ") || "Could not send verification email. Contact the operator."
                    : res.error === "signup_disabled"
                      ? "Sign-up is disabled on this deployment."
                      : "Couldn't sign in. Check your details and retry.";
      setError(msg);
    }
  }, [email, password, name, mode, onAuthed]);

  const resend = useCallback(async () => {
    setBusy(true);
    setResendMsg("");
    const res = await resendVerificationEmail(email.trim());
    setBusy(false);
    setResendMsg(
      res.ok
        ? "Verification email sent."
        : [res.detail, res.hint].filter(Boolean).join(" — ") || "Could not resend — try again shortly.",
    );
  }, [email]);

  // Either gate hides the form and shows a status panel instead.
  const awaitingAction = pendingVerification || pendingApproval;

  return (
    <div style={cardShell}>
      <div style={card}>
        <div style={{ fontSize: 11, letterSpacing: "0.18em", fontWeight: 700, color: "var(--aethos-text-dim)" }}>
          AETHOS
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "8px 0 4px" }}>
          {mode === "register" ? "Create your account" : "Sign in"}
        </h1>
        <p style={{ fontSize: 13, color: "var(--aethos-text-muted)", margin: 0 }}>
          Your keys, your models, your data — isolated from every other tenant.
        </p>

        {awaitingAction ? (
          <div style={{ marginTop: 18, fontSize: 13, color: "var(--aethos-text-muted)" }}>
            {pendingApproval ? (
              <p style={{ margin: "0 0 10px" }}>
                Your previous access ended, so we re-registered you.{" "}
                {pendingVerification ? (
                  <>
                    Verify your email at <strong>{email}</strong>, then your account is{" "}
                    <strong>pending approval</strong> — you can sign in once access is granted.
                  </>
                ) : (
                  <>
                    Your account is <strong>pending approval</strong> — you can sign in once access is granted.
                  </>
                )}
              </p>
            ) : (
              <p style={{ margin: "0 0 10px" }}>
                Check your inbox for a verification link sent to <strong>{email}</strong>. You must verify before
                signing in.
              </p>
            )}
            {resendMsg ? <p style={{ margin: "0 0 10px", color: "var(--aethos-accent)" }}>{resendMsg}</p> : null}
            {pendingVerification ? (
              <button type="button" style={primaryBtn} disabled={busy} onClick={() => void resend()}>
                Resend verification email
              </button>
            ) : null}
            <button
              type="button"
              style={{
                width: "100%",
                marginTop: 12,
                padding: 8,
                border: "none",
                background: "transparent",
                color: "var(--aethos-text-muted)",
                fontSize: 13,
                cursor: "pointer",
              }}
              onClick={() => {
                setPendingVerification(false);
                setPendingApproval(false);
                setMode("login");
              }}
            >
              Back to sign in
            </button>
          </div>
        ) : null}

        {!awaitingAction && mode === "register" ? (
          <>
            <label style={fieldLabel} htmlFor="reg-name">Name</label>
            <input id="reg-name" value={name} style={inputStyle} onChange={(e) => setName(e.target.value)} placeholder="Optional" />
          </>
        ) : null}

        {!awaitingAction ? (
          <>
            <label style={fieldLabel} htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              autoFocus
              value={email}
              style={inputStyle}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />

            <label style={fieldLabel} htmlFor="auth-pass">Password</label>
            <input
              id="auth-pass"
              type="password"
              value={password}
              style={inputStyle}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void submit();
              }}
            />

            {error ? <div style={{ color: "var(--aethos-danger)", fontSize: 12, marginTop: 10 }}>{error}</div> : null}

            <button
              type="button"
              style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}
              disabled={busy}
              onClick={() => void submit()}
            >
              {busy ? "Working…" : mode === "register" ? "Create account" : "Sign in"}
            </button>
          </>
        ) : null}

        {!awaitingAction && selfSignupEnabled ? (
          <button
            type="button"
            style={{
              width: "100%",
              marginTop: 12,
              padding: 8,
              border: "none",
              background: "transparent",
              color: "var(--aethos-text-muted)",
              fontSize: 13,
              cursor: "pointer",
            }}
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account? Sign up" : "Already have an account? Sign in"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
