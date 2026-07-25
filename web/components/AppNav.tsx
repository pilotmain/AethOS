import Link from "next/link";

type NavActive =
  | "chat"
  | "mission-control"
  | "canvas"
  | "workspace"
  | "skills"
  | "research"
  | "foundry"
  | "email"
  | "calendar"
  | "notes";

type Props = {
  active: NavActive;
};

const NAV_ITEMS: { id: NavActive; href: string; label: string; prefetchChunk?: () => void }[] = [
  { id: "chat", href: "/", label: "Chat" },
  { id: "research", href: "/workspace/research", label: "Research" },
  { id: "workspace", href: "/workspace/documents", label: "Documents" },
  { id: "foundry", href: "/workspace/foundry", label: "Foundry" },
  { id: "email", href: "/workspace/email", label: "Email" },
  { id: "calendar", href: "/workspace/calendar", label: "Calendar" },
  { id: "notes", href: "/workspace/notes", label: "Notes" },
  { id: "skills", href: "/skills", label: "Skills" },
  {
    id: "mission-control",
    href: "/mission-control",
    label: "Mission Control",
    prefetchChunk: () => void import("@/components/MissionControlShell"),
  },
  { id: "canvas", href: "/canvas", label: "Canvas" },
];

export function prefetchMissionControlChunk(): void {
  void import("@/components/MissionControlShell");
}

export function AppNav({ active }: Props) {
  const linkStyle = (isActive: boolean) => ({
    fontSize: 13,
    color: isActive ? "var(--aethos-accent)" : "var(--aethos-text-muted)",
    textDecoration: "none",
    fontWeight: isActive ? 600 : 400,
    padding: "3px 6px",
    borderRadius: 6,
    outlineOffset: 2,
    transition: "color 120ms ease",
  });

  return (
    <nav aria-label="Primary" style={{ display: "flex", gap: 12, marginTop: 10, flexWrap: "wrap" }}>
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.id}
          href={item.href}
          prefetch={true}
          aria-current={active === item.id ? "page" : undefined}
          style={linkStyle(active === item.id)}
          onMouseEnter={item.prefetchChunk}
          onFocus={item.prefetchChunk}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
