"use client";

import { mcColors } from "@/lib/missionControl/layout";

type Props = {
  label?: string;
  onClick: () => void;
};

/** Read-only navigation into job replay — never triggers execution. */
export function ReplayDeepLinkButton({ label = "View in replay →", onClick }: Props) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      style={{
        marginTop: 6,
        padding: 0,
        border: "none",
        background: "none",
        color: mcColors.cyan,
        fontSize: 11,
        cursor: "pointer",
        textAlign: "left",
      }}
    >
      {label}
    </button>
  );
}
