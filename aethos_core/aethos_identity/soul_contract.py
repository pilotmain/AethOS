# SPDX-License-Identifier: Apache-2.0
"""Load AethOS soul doctrines from SOUL.md."""

from __future__ import annotations


def clear_soul_contract_cache() -> None:
    from aethos_core.aethos_identity.identity_contract_loader import invalidate_identity_contract_cache

    invalidate_identity_contract_cache()


def load_soul_markdown() -> str:
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    return load_identity_contracts().soul.content


def soul_doctrines() -> list[str]:
    text = load_soul_markdown()
    doctrines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**When ") and stripped.endswith("**"):
            doctrines.append(stripped.strip("*"))
    return doctrines


def reconstruct_before_asking() -> bool:
    from aethos_core.aethos_identity.identity_contract_loader import reconstruct_before_amnesia_required

    return reconstruct_before_amnesia_required()


def avoid_generic_operational_fallback() -> bool:
    from aethos_core.aethos_identity.identity_contract_loader import generic_operational_fallback_forbidden

    return generic_operational_fallback_forbidden()
