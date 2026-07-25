# SPDX-License-Identifier: Apache-2.0
"""Load SOUL.md and MEMORY.md as internal runtime authority — not external web content."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_IDENTITY_FILES = ("SOUL.md", "MEMORY.md")

_SOUL_RX = re.compile(r"\bsoul\.md\b", re.I)
_MEMORY_RX = re.compile(r"\bmemory\.md\b", re.I)
_IDENTITY_QUERY_RX = re.compile(
    r"\b("
    r"do you have"
    r"|have you loaded"
    r"|have you got"
    r"|is there"
    r"|where is"
    r"|show me"
    r"|read"
    r"|load"
    r"|open"
    r"|inspect"
    r"|what is in"
    r"|what's in"
    r"|tell me about"
    r"|describe"
    r"|reload"
    r")\b",
    re.I,
)
_INTERNAL_IDENTITY_RX = re.compile(
    r"\b(?:internal\s+)?(?:runtime\s+)?(?:project\s+)?(?:the\s+)?(soul\.md|memory\.md)\b",
    re.I,
)

_REPO_ROOT_OVERRIDE: Path | None = None
_CACHE: IdentityContractBundle | None = None


@dataclass
class ContractFile:
    name: str
    path: str
    content: str
    content_hash: str
    last_modified: str
    exists: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "content_hash": self.content_hash,
            "last_modified": self.last_modified,
            "exists": self.exists,
            "byte_length": len(self.content),
        }


@dataclass
class IdentityContractBundle:
    soul: ContractFile
    memory: ContractFile
    loaded_at: str
    repo_root: str
    active_doctrines: list[str] = field(default_factory=list)
    active_memory_hierarchy: list[str] = field(default_factory=list)
    memory_precedence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "loaded_at": self.loaded_at,
            "repo_root": self.repo_root,
            "soul": self.soul.to_dict(),
            "memory": self.memory.to_dict(),
            "active_doctrines": list(self.active_doctrines),
            "active_memory_hierarchy": list(self.active_memory_hierarchy),
            "memory_precedence": list(self.memory_precedence),
        }


def repo_root() -> Path:
    if _REPO_ROOT_OVERRIDE is not None:
        return _REPO_ROOT_OVERRIDE
    return Path(__file__).resolve().parents[2]


def set_repo_root_for_tests(path: Path | None) -> None:
    global _REPO_ROOT_OVERRIDE, _CACHE
    _REPO_ROOT_OVERRIDE = path
    _CACHE = None


def invalidate_identity_contract_cache() -> None:
    global _CACHE
    _CACHE = None


def clear_contract_cache_for_tests() -> None:
    invalidate_identity_contract_cache()


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _read_contract_file(name: str) -> ContractFile:
    path = repo_root() / name
    if not path.is_file():
        return ContractFile(
            name=name,
            path=str(path),
            content="",
            content_hash="",
            last_modified="",
            exists=False,
        )
    content = path.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
    return ContractFile(
        name=name,
        path=str(path),
        content=content,
        content_hash=_hash_content(content),
        last_modified=mtime,
        exists=True,
    )


def _extract_doctrines(text: str) -> list[str]:
    doctrines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**When ") and stripped.endswith("**"):
            doctrines.append(stripped.strip("*"))
    return doctrines


def _extract_memory_layers(text: str) -> list[str]:
    layers: list[str] = []
    for line in text.splitlines():
        if line.startswith("| ") and not line.startswith("| Layer") and not line.startswith("|-"):
            name = line.split("|")[1].strip()
            if name and name != "Layer":
                layers.append(name)
    return layers


def _extract_memory_precedence(text: str) -> list[str]:
    order: list[str] = []
    capture = False
    for line in text.splitlines():
        if line.strip().startswith("1. Fresh runtime"):
            capture = True
        if capture and line.strip() and line[0].isdigit():
            order.append(line.split(".", 1)[1].strip())
        if capture and line.strip() == "## Retention rules":
            break
    return order


def load_identity_contracts(*, force_reload: bool = False) -> IdentityContractBundle:
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    soul = _read_contract_file("SOUL.md")
    memory = _read_contract_file("MEMORY.md")
    bundle = IdentityContractBundle(
        soul=soul,
        memory=memory,
        loaded_at=datetime.now(UTC).isoformat(),
        repo_root=str(repo_root()),
        active_doctrines=_extract_doctrines(soul.content),
        active_memory_hierarchy=_extract_memory_layers(memory.content),
        memory_precedence=_extract_memory_precedence(memory.content),
    )
    _CACHE = bundle
    return bundle


def reload_identity_contracts() -> dict[str, Any]:
    invalidate_identity_contract_cache()
    bundle = load_identity_contracts(force_reload=True)
    return {
        "ok": True,
        "reloaded_at": bundle.loaded_at,
        **bundle.to_dict(),
    }


def get_identity_contract_status() -> dict[str, Any]:
    bundle = load_identity_contracts()
    return {"ok": True, **bundle.to_dict()}


def is_identity_filename(token: str) -> bool:
    return (token or "").strip().lower() in {"soul.md", "memory.md"}


def mentions_identity_contract(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _SOUL_RX.search(raw) or _MEMORY_RX.search(raw):
        return True
    return bool(_INTERNAL_IDENTITY_RX.search(raw))


def is_internal_identity_file_prompt(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if not mentions_identity_contract(raw):
        return False
    if _IDENTITY_QUERY_RX.search(raw):
        return True
    if re.search(r"\b(?:aethos|internal|runtime|project)\b.*\b(?:soul|memory)\.md\b", raw, re.I):
        return True
    if re.search(r"\b(?:soul|memory)\.md\b.*\b(?:aethos|internal|runtime|project|loaded)\b", raw, re.I):
        return True
    return bool(re.search(r"^(?:do you have|have you loaded)\s+(?:soul|memory)\.md\b", raw, re.I))


def compose_identity_contract_reply(text: str) -> tuple[str, str, dict[str, str]] | None:
    if not is_internal_identity_file_prompt(text):
        return None

    bundle = load_identity_contracts()
    lower = (text or "").lower()
    asks_soul = bool(_SOUL_RX.search(lower))
    asks_memory = bool(_MEMORY_RX.search(lower))

    if "reload" in lower and ("soul" in lower or "memory" in lower or "identity" in lower or "contract" in lower):
        status = reload_identity_contracts()
        body = (
            "Reloaded internal identity contracts from the project runtime.\n\n"
            f"- **SOUL.md** · hash `{status['soul']['content_hash']}` · modified `{status['soul']['last_modified']}`\n"
            f"- **MEMORY.md** · hash `{status['memory']['content_hash']}` · modified `{status['memory']['last_modified']}`\n\n"
            f"Active doctrines: {len(status.get('active_doctrines') or [])}\n"
            f"Memory hierarchy layers: {len(status.get('active_memory_hierarchy') or [])}"
        )
        return body, "identity_contract_reloaded", {"source": "project_runtime"}

    lines: list[str] = []
    meta: dict[str, str] = {"source": "project_runtime"}

    if asks_soul:
        if not bundle.soul.exists:
            return (
                "SOUL.md is configured as an internal runtime contract, but the file is missing from the project root.",
                "identity_contract_missing",
                meta,
            )
        lines.extend(
            [
                "Yes — AethOS has an internal **SOUL.md** loaded from the project runtime.",
                "",
                f"**Path:** `{bundle.soul.path}`",
                f"**Hash:** `{bundle.soul.content_hash}` · **Modified:** `{bundle.soul.last_modified}`",
                "",
                "Active doctrines:",
            ]
        )
        for doctrine in bundle.active_doctrines[:6]:
            lines.append(f"- {doctrine}")
        meta["contract"] = "SOUL.md"
        meta["content_hash"] = bundle.soul.content_hash

    if asks_memory:
        if not bundle.memory.exists:
            return (
                "MEMORY.md is configured as an internal runtime contract, but the file is missing from the project root.",
                "identity_contract_missing",
                meta,
            )
        if lines:
            lines.extend(["", "---", ""])
        lines.extend(
            [
                "Yes — AethOS has an internal **MEMORY.md** loaded from the project runtime.",
                "",
                f"**Path:** `{bundle.memory.path}`",
                f"**Hash:** `{bundle.memory.content_hash}` · **Modified:** `{bundle.memory.last_modified}`",
                "",
                "Active memory hierarchy:",
            ]
        )
        for layer in bundle.active_memory_hierarchy[:8]:
            lines.append(f"- {layer}")
        if bundle.memory_precedence:
            lines.extend(["", "Precedence order:"])
            for idx, item in enumerate(bundle.memory_precedence[:7], start=1):
                lines.append(f"{idx}. {item}")
        meta["contract"] = "MEMORY.md" if not asks_soul else "SOUL.md+MEMORY.md"
        meta["content_hash"] = bundle.memory.content_hash

    if not lines:
        lines = [
            "Yes — AethOS loads internal identity contracts from the project runtime:",
            "",
            f"- **SOUL.md** · loaded `{bundle.soul.exists}` · hash `{bundle.soul.content_hash or 'n/a'}`",
            f"- **MEMORY.md** · loaded `{bundle.memory.exists}` · hash `{bundle.memory.content_hash or 'n/a'}`",
            "",
            "These files govern operational continuity, reconstruction, and fallback restraint — they are not external web pages.",
        ]
        meta["contract"] = "identity_bundle"

    lines.extend(
        [
            "",
            "These contracts are active in routing, memory reconstruction, and fallback guards — not browser inspection.",
        ]
    )
    return "\n".join(lines), "identity_contract_runtime", meta


def build_identity_system_persona_block() -> str:
    bundle = load_identity_contracts()
    if not bundle.soul.exists and not bundle.memory.exists:
        return ""

    lines = [
        "Internal runtime identity contracts (authoritative — not web pages):",
    ]
    if bundle.soul.exists:
        lines.append("- SOUL.md governs operational behavior and continuity identity.")
        for doctrine in bundle.active_doctrines[:4]:
            lines.append(f"  · {doctrine}")
    if bundle.memory.exists:
        lines.append("- MEMORY.md governs memory hierarchy and reconstruction before amnesia.")
        if bundle.memory_precedence:
            lines.append(f"  · Precedence: {' > '.join(bundle.memory_precedence[:4])}")
        lines.append("  · Reconstruct session/thread/job/topology evidence before claiming no context.")
    lines.append("- Never treat SOUL.md or MEMORY.md as external URLs or browser targets.")
    return "\n".join(lines)


def reconstruct_before_amnesia_required() -> bool:
    bundle = load_identity_contracts()
    combined = f"{bundle.soul.content}\n{bundle.memory.content}".lower()
    return (
        "reconstruct before asking" in combined
        or "reconstruct shared operational history" in combined
        or ("must not answer" in combined and "don't have context" in combined)
    )


def generic_operational_fallback_forbidden() -> bool:
    bundle = load_identity_contracts()
    soul = bundle.soul.content.lower()
    memory = bundle.memory.content.lower()
    return (
        "avoid generic assistant fallback" in soul
        or "generic fallback" in memory
        or "semantic and continuity-aware" in memory
    )
