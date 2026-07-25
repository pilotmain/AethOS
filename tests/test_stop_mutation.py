# SPDX-License-Identifier: Apache-2.0
"""Governed stop mutation — target extraction and registry-first resolution."""

from __future__ import annotations

from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent, has_explicit_mutation_verb
from aethos_core.operations.mutations.stop_mutation import (
    extract_stop_target_names,
    resolve_stop_target,
    resolve_stop_targets,
)


def test_stop_is_explicit_mutation_verb():
    assert has_explicit_mutation_verb("stop invoice-pilot on railway")


def test_extract_multiple_stop_targets():
    text = "Stop the following project\n\npilot-command-center\ninvoicepilot\nkillit"
    names = extract_stop_target_names(text)
    assert "pilot-command-center" in names
    assert "invoicepilot" in names
    assert "killit" in names


def test_registry_resolves_invoicepilot():
    row = resolve_stop_target("invoicepilot")
    assert row.status == "resolved"
    assert row.target_name == "invoicepilot"
    assert row.provider == "vercel"


def test_registry_resolves_pilot_command_center():
    row = resolve_stop_target("pilot-command-center")
    assert row.status == "resolved"
    assert row.provider == "vercel"
    assert row.target_name == "pilot-command-center"


def test_registry_resolves_killit():
    row = resolve_stop_target("killit")
    assert row.status == "resolved"
    assert row.provider == "vercel"
    assert row.target_name == "killit"


def test_detect_stop_intent():
    intent = detect_explicit_mutation_intent("stop invoice-pilot")
    assert intent is not None
    assert intent.operation == "stop"


def test_resolve_stop_targets_batch_unknown(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.deployment_targets.registry.find_target_by_alias",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_inference.find_target_in_vercel_inventory",
        lambda _hint: None,
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_inference.find_target_in_railway_inventory",
        lambda _hint: None,
    )
    batch = resolve_stop_targets(["missing-name-xyz"])
    assert batch.targets[0].status == "not_found"


def test_stop_outcome_question_skips_preflight_creation():
    from aethos_core.operations.mutations.stop_mutation import compose_stop_mutation_preflight_reply, is_stop_outcome_question

    assert is_stop_outcome_question("did you stop the projects.service?")
    assert compose_stop_mutation_preflight_reply("did you stop the projects.service?", session_id="s1") is None


def test_extract_stop_ignores_question_words():
    names = extract_stop_target_names("did you stop the projects.service?")
    assert names == []
