# SPDX-License-Identifier: Apache-2.0
"""Load AethOS memory hierarchy rules from MEMORY.md."""

from __future__ import annotations


def clear_memory_contract_cache() -> None:
    from aethos_core.aethos_identity.identity_contract_loader import invalidate_identity_contract_cache

    invalidate_identity_contract_cache()


def load_memory_markdown() -> str:
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    return load_identity_contracts().memory.content


def memory_layers() -> list[str]:
    layers: list[str] = []
    for line in load_memory_markdown().splitlines():
        if line.startswith("| ") and not line.startswith("| Layer") and not line.startswith("|-"):
            name = line.split("|")[1].strip()
            if name and name != "Layer":
                layers.append(name)
    return layers


def memory_precedence() -> list[str]:
    text = load_memory_markdown()
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


def must_reconstruct_before_no_context() -> bool:
    return "must not answer" in load_memory_markdown().lower() and "don't have context" in load_memory_markdown().lower()
