"use client";

import { useId } from "react";

/**
 * AethOS logo mark — a cyan→violet "A" monogram with circuit nodes, matching the
 * brand's signature gradient. Scales cleanly (SVG) and themes via the fixed brand
 * colors (intentionally constant across light/dark so the mark stays recognizable).
 */
export function AethosLogo({ size = 28, title = "AethOS" }: { size?: number; title?: string }) {
  const gid = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      role="img"
      aria-label={title}
      style={{ flexShrink: 0 }}
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="48" x2="48" y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
      </defs>
      {/* Solid 'A' monogram — hollow triangle (evenodd) + crossbar. */}
      <path fill={`url(#${gid})`} fillRule="evenodd" d="M24 5 L45 43 L3 43 Z M24 18 L36 39 L12 39 Z" />
      <rect x="15" y="30" width="18" height="5" rx="1.5" fill={`url(#${gid})`} />
    </svg>
  );
}
