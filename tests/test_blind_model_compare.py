# SPDX-License-Identifier: Apache-2.0
"""Blind model compare (§B2)."""

from __future__ import annotations

from aethos_core.research.blind_model_eval import run_blind_model_eval


def test_blind_compare_anonymized_until_reveal():
    out = run_blind_model_eval(prompt="Explain governed agent deployments in two sentences.")
    assert out.get("ok") is True
    slots = out.get("blind_slots") or []
    assert len(slots) >= 2
    for slot in slots:
        assert "slot_id" in slot and slot.get("text")
    assert out.get("reveal_map")
