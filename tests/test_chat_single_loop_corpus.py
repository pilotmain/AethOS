# SPDX-License-Identifier: Apache-2.0
"""Permanent single-loop acceptance corpus — AETHOS_ONE_LOOP_AND_FAST_LOAD.md §5."""

from __future__ import annotations

from tests.test_chat_layer_rebuild_corpus import (
    test_single_loop_canvas_render_command,
    test_single_loop_corpus_pilotmain_and_two_page,
    test_single_loop_mutation_gate_blocks_scramble,
    test_single_loop_no_governance_footer_on_writing_turn,
    test_single_loop_rest_nudge_not_on_every_reply,
    test_single_loop_subject_persists_with_memory_only,
)

__all__ = [
    "test_single_loop_corpus_pilotmain_and_two_page",
    "test_single_loop_no_governance_footer_on_writing_turn",
    "test_single_loop_rest_nudge_not_on_every_reply",
    "test_single_loop_canvas_render_command",
    "test_single_loop_mutation_gate_blocks_scramble",
    "test_single_loop_subject_persists_with_memory_only",
]
