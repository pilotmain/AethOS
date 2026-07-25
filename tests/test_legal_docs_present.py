# SPDX-License-Identifier: Apache-2.0
"""Public-release gate for the project's open-source legal documents."""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name",
    [
        "LICENSE",
        "NOTICE",
        "LICENSING.md",
        "COPYRIGHT.md",
        "CONTRIBUTING.md",
        "DCO.md",
        "DISCLAIMER.md",
    ],
)
def test_legal_file_present(name):
    assert (_ROOT / name).is_file(), f"{name} missing"


def test_license_is_apache_2_0():
    txt = (_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in txt
    assert "Version 2.0, January 2004" in txt
    assert "END OF TERMS AND CONDITIONS" in txt


def test_notice_states_original_work_attribution():
    txt = (_ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "AethOS" in txt
    assert "Copyright 2026 Raya Meresa" in txt
    assert "Copyright 2026 PilotMain LLC" in txt
    assert "Thirsty's Projects LLC" not in txt


def test_disclaimer_has_core_protections():
    txt = (_ROOT / "DISCLAIMER.md").read_text(encoding="utf-8")
    assert "AS IS" in txt  # no-warranty
    assert "responsible for what you approve" in txt.lower()  # operator owns approved actions


def test_licensing_is_consistent_with_repository_headers():
    txt = (_ROOT / "LICENSING.md").read_text(encoding="utf-8").lower()
    assert "apache-2.0" in txt
    assert "source-available" not in txt
    assert "all rights reserved" not in txt


def test_contributions_use_dco_without_assignment():
    contributing = (_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8").lower()
    copyright_policy = (_ROOT / "COPYRIGHT.md").read_text(encoding="utf-8").lower()
    assert "signed-off-by" in contributing
    assert "retain copyright" in copyright_policy
    assert "copyright assignment" in copyright_policy
