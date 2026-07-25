# SPDX-License-Identifier: Apache-2.0
"""Repo reference parser tests."""

from __future__ import annotations

from aethos_core.provider_topology.repo_reference_parser import parse_repo_reference


def test_full_github_url():
    ref = parse_repo_reference("can you check in https://github.com/pilotmain/speakglobal-ai/ instead")
    assert ref is not None
    assert ref.full_name == "pilotmain/speakglobal-ai"
    assert ref.confidence >= 0.95


def test_github_com_without_scheme():
    ref = parse_repo_reference("look at github.com/pilotmain/speakglobal-ai")
    assert ref is not None
    assert ref.full_name == "pilotmain/speakglobal-ai"


def test_owner_repo():
    ref = parse_repo_reference("use pilotmain/speakglobal-ai instead")
    assert ref is not None
    assert ref.full_name == "pilotmain/speakglobal-ai"


def test_use_owner_repo_instead():
    ref = parse_repo_reference("please use pilotmain/speakglobal-ai instead")
    assert ref is not None
    assert ref.owner == "pilotmain"
    assert ref.repo == "speakglobal-ai"


def test_non_repo_text_ignored():
    ref = parse_repo_reference("can you check and report back?")
    assert ref is None


def test_railway_restart_repo_target():
    ref = parse_repo_reference("restart railway pilotmain/speakglobal-ai service")
    assert ref is not None
    assert ref.full_name == "pilotmain/speakglobal-ai"
    assert ref.source == "railway_restart_repo"
