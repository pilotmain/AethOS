# SPDX-License-Identifier: Apache-2.0
"""CLI brand constants."""

from aethos_core.cli.brand import (
    AETHOS_EVIDENCE,
    AETHOS_MUTATION,
    AETHOS_PRIMARY,
    AETHOS_SUCCESS,
    AETHOS_WARNING,
    BrandTone,
    aethos_log,
    format_banner,
    format_section,
    strip_ansi,
)


def test_brand_constants_defined():
    assert AETHOS_PRIMARY.startswith("\033[")
    assert AETHOS_SUCCESS.startswith("\033[")
    assert AETHOS_WARNING.startswith("\033[")
    assert AETHOS_MUTATION.startswith("\033[")
    assert AETHOS_EVIDENCE.startswith("\033[")


def test_aethos_log_prefix():
    line = aethos_log("Initializing orchestration runtime", tone=BrandTone.PRIMARY)
    assert "[AethOS]" in strip_ansi(line)
    assert "Initializing orchestration runtime" in strip_ansi(line)


def test_format_banner():
    banner = format_banner(version="0.2.0")
    plain = strip_ansi(banner)
    assert "AethOS" in plain
    assert "0.2.0" in plain


def test_format_section():
    section = format_section("Preflight")
    assert "Preflight" in strip_ansi(section)
