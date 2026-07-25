"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { verifyEmailToken } from "@/lib/onboarding/tenantSetup";

export default function VerifyEmailPage() {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") || "";
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token.");
      return;
    }
    void verifyEmailToken(token).then((res) => {
      if (res.ok) {
        setStatus("ok");
        setMessage("Email verified. You can sign in to AethOS now.");
      } else {
        setStatus("error");
        setMessage(
          res.error === "token_expired"
            ? "This link expired. Sign in and request a new verification email."
            : "This verification link is invalid or already used.",
        );
      }
    });
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "var(--aethos-bg-deep)",
        color: "var(--aethos-text)",
      }}
    >
      <div
        style={{
          maxWidth: 420,
          padding: 28,
          borderRadius: 16,
          border: "1px solid var(--aethos-border)",
          background: "var(--aethos-surface-strong)",
        }}
      >
        <h1 style={{ fontSize: 20, margin: "0 0 8px" }}>Email verification</h1>
        <p style={{ fontSize: 14, color: "var(--aethos-text-muted)", margin: 0 }}>
          {status === "loading" ? "Verifying…" : message}
        </p>
        {status === "ok" ? (
          <Link
            href="/?verified=1"
            style={{
              display: "inline-block",
              marginTop: 16,
              fontSize: 14,
              fontWeight: 600,
              color: "var(--aethos-accent)",
            }}
          >
            Sign in to AethOS
          </Link>
        ) : null}
      </div>
    </main>
  );
}
