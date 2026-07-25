"use client";

import Link from "next/link";

export type WorkspaceTab = "documents" | "notes" | "foundry" | "email" | "calendar";

const TABS: { id: WorkspaceTab; label: string; href: string }[] = [
  { id: "documents", label: "Documents", href: "/workspace/documents" },
  { id: "notes", label: "Notes & Tasks", href: "/workspace/notes" },
  { id: "foundry", label: "Model Foundry", href: "/workspace/foundry" },
  { id: "email", label: "Email", href: "/workspace/email" },
  { id: "calendar", label: "Calendar", href: "/workspace/calendar" },
];

export function WorkspaceNav({ active }: { active: WorkspaceTab }) {
  return (
    <nav style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
      {TABS.map((t) => {
        const isActive = t.id === active;
        return (
          <Link
            key={t.id}
            href={t.href}
            style={{
              fontSize: 12,
              padding: "6px 12px",
              borderRadius: 999,
              textDecoration: "none",
              border: `1px solid ${isActive ? "var(--aethos-accent)" : "var(--aethos-border)"}`,
              background: isActive ? "var(--aethos-accent-soft)" : "var(--aethos-surface)",
              color: isActive ? "var(--aethos-text)" : "var(--aethos-text-muted)",
              fontWeight: isActive ? 600 : 400,
            }}
          >
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}
