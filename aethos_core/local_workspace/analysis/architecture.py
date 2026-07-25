# SPDX-License-Identifier: Apache-2.0
"""Semantic architecture map generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_LAYER_HINTS: list[tuple[str, list[str], str]] = [
    ("Mission Control UI", ["web/components", "web/app"], "frontend operational console"),
    ("Chat workspace", ["web/components/chat", "web/components/ChatShell"], "conversation + lifecycle UX"),
    ("API layer", ["aethos_core/api"], "FastAPI routes and handlers"),
    ("Orchestration brain", ["aethos_core/operations/orchestration", "aethos_core/chat"], "intent routing and preflight"),
    ("Mutation governance", ["aethos_core/operations/mutations"], "approval, blast radius, execution"),
    ("Provider runtime", ["aethos_core/operations/orchestration/provider_runtime"], "unified provider auth + execution"),
    ("Provider adapters", ["aethos_core/providers"], "Railway, GitHub, Vercel adapters"),
    ("Browser evidence", ["aethos_core/browser"], "governed capture, artifacts, policy"),
    ("Credential vault", ["aethos_core/security", "aethos_core/connections"], "encrypted persistence + hydration"),
    ("Local workspace", ["aethos_core/local_workspace", "aethos_core/local_repo"], "repo intelligence substrate"),
    ("Job runtime", ["aethos_core/runtime"], "jobs, executor, authority"),
]

_SEMANTIC_FILE_HINTS: list[tuple[str, str, str]] = [
    (r"provider_runtime", "Provider runtime layer", "orchestration runtime"),
    (r"browser_capture|browser_evidence|browser_runtime", "Governed browser evidence engine", "browser evidence"),
    (r"mutation_execution|mutation_preflight|mutation_governance", "Governed mutation execution lifecycle", "mutation governance"),
    (r"engineering_intelligence|local_workspace", "Local workspace intelligence substrate", "engineering substrate"),
    (r"MissionControl|mission_control", "Mission Control UI", "operational console"),
    (r"credential_vault|credential_paths", "Credential vault", "security"),
]


def analyze_architecture(repo: Path) -> dict[str, Any]:
    layers: list[dict[str, Any]] = []
    for name, rel_paths, role in _LAYER_HINTS:
        hits = [p for p in rel_paths if (repo / p).exists()]
        if hits:
            layers.append({"layer": name, "paths": hits, "role": role, "present": True})
        else:
            layers.append({"layer": name, "paths": rel_paths, "role": role, "present": False})

    semantic_modules = _scan_semantic_modules(repo)
    present = [l for l in layers if l["present"]]

    flow = [
        "channel → orchestration → lifecycle → policy → governed capture → artifacts → MC → audit",
        "connect → encrypt → persist → hydrate → validate → runtime auth → orchestration",
    ]
    if any(l["present"] for l in layers if l["layer"] == "Browser evidence"):
        flow.append("intent → provider inference → URL resolution → browser capture OR metadata-only → audit")
    if semantic_modules:
        flow.append(" → ".join(m["label"] for m in semantic_modules[:5]))

    graph = _build_architecture_graph(present, semantic_modules)

    return {
        "ok": True,
        "repo": str(repo),
        "layers": present,
        "missing_layers": [l["layer"] for l in layers if not l["present"]],
        "semantic_modules": semantic_modules,
        "operational_flows": flow,
        "architecture_graph": graph,
        "summary": _summarize_layers(present, semantic_modules),
    }


def format_architecture_report(analysis: dict[str, Any]) -> str:
    lines = [
        "# Architecture analysis (readonly)",
        "",
        f"**Repo:** `{analysis.get('repo')}`",
        "",
        "## Detected layers",
    ]
    for layer in analysis.get("layers") or []:
        lines.append(f"- **{layer['layer']}** — {layer['role']}")
        lines.append(f"  - paths: {', '.join('`' + p + '`' for p in layer.get('paths') or [])}")
    semantic = analysis.get("semantic_modules") or []
    if semantic:
        lines.extend(["", "## Semantic modules"])
        for mod in semantic:
            lines.append(f"- **{mod.get('label')}** — `{mod.get('path')}` ({mod.get('category')})")
    graph = analysis.get("architecture_graph") or []
    if graph:
        lines.extend(["", "## Architecture graph"])
        for edge in graph:
            lines.append(f"- {edge}")
    lines.extend(["", "## Operational flows"])
    for flow in analysis.get("operational_flows") or []:
        lines.append(f"- {flow}")
    lines.extend(["", analysis.get("summary") or ""])
    return "\n".join(lines)


def _scan_semantic_modules(repo: Path, *, limit: int = 16) -> list[dict[str, str]]:
    from aethos_core.local_workspace.canonical_path import iter_repo_files_limited

    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in iter_repo_files_limited(repo, max_depth=8):
        if len(found) >= limit:
            break
        name = path.name
        rel = str(path.relative_to(repo))
        for pattern, label, category in _SEMANTIC_FILE_HINTS:
            if pattern in name or re.search(pattern, rel, re.I):
                key = label
                if key in seen:
                    break
                seen.add(key)
                found.append(
                    {
                        "label": label,
                        "path": str(path.relative_to(repo)),
                        "category": category,
                    }
                )
                break
    return found


def _build_architecture_graph(
    layers: list[dict[str, Any]], semantic: list[dict[str, str]]
) -> list[str]:
    names = [str(l.get("layer") or "") for l in layers]
    edges: list[str] = []
    if "Chat workspace" in names and "Orchestration brain" in names:
        edges.append("Chat workspace → Orchestration brain → Policy")
    if "Orchestration brain" in names and "Provider runtime" in names:
        edges.append("Orchestration brain → Provider runtime → Provider adapters")
    if "Browser evidence" in names:
        edges.append("Intent → Browser evidence → Artifacts → Mission Control UI")
    if "Mutation governance" in names:
        edges.append("Mutation preflight → Approval → Mutation governance → Verification → Audit")
    if "Local workspace" in names:
        edges.append("Engineering intent → Local workspace → Artifacts → Engineering memory")
    for mod in semantic[:4]:
        edges.append(f"Module `{mod.get('path')}` → {mod.get('label')}")
    return edges[:10]


def _summarize_layers(present: list[dict[str, Any]], semantic: list[dict[str, str]]) -> str:
    names = [str(l.get("layer") or "") for l in present[:8]]
    if semantic:
        sem = ", ".join(m["label"] for m in semantic[:4])
        extra = f" Semantic: {sem}."
    else:
        extra = ""
    if not names:
        return "No known architecture layers detected in this workspace." + extra
    return (
        "Architecture map: "
        + " → ".join(names[:6])
        + (" …" if len(names) > 6 else "")
        + ". Readonly semantic scan — not a file tree dump."
        + extra
    )
