# SPDX-License-Identifier: Apache-2.0
"""Terminal brand system — unified identity for installer, CLI, and runtime logs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BrandTone(str, Enum):
    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    MUTATION = "mutation"
    EVIDENCE = "evidence"
    MUTED = "muted"


# ANSI sequences — dark-mode native, restrained saturation
AETHOS_PRIMARY = "\033[38;5;45m"  # cyan — governance / identity
AETHOS_SUCCESS = "\033[38;5;42m"  # emerald — stable runtime
AETHOS_WARNING = "\033[38;5;220m"  # amber — experimental / caution
AETHOS_MUTATION = "\033[38;5;203m"  # red-toned — governed mutations
AETHOS_EVIDENCE = "\033[38;5;51m"  # bright cyan — evidence capture
AETHOS_SLATE = "\033[38;5;245m"  # slate — enterprise neutral
AETHOS_BOLD = "\033[1m"
AETHOS_RESET = "\033[0m"
AETHOS_DIM = "\033[2m"

_PREFIX = f"{AETHOS_PRIMARY}[AethOS]{AETHOS_RESET}"

_TONE_MAP: dict[BrandTone, str] = {
    BrandTone.PRIMARY: AETHOS_PRIMARY,
    BrandTone.SUCCESS: AETHOS_SUCCESS,
    BrandTone.WARNING: AETHOS_WARNING,
    BrandTone.MUTATION: AETHOS_MUTATION,
    BrandTone.EVIDENCE: AETHOS_EVIDENCE,
    BrandTone.MUTED: AETHOS_SLATE,
}


@dataclass(frozen=True)
class BrandMessage:
    text: str
    tone: BrandTone = BrandTone.PRIMARY


def _tone_color(tone: BrandTone) -> str:
    return _TONE_MAP.get(tone, AETHOS_PRIMARY)


def aethos_log(message: str, *, tone: BrandTone = BrandTone.PRIMARY) -> str:
    color = _tone_color(tone)
    return f"{_PREFIX} {color}{message}{AETHOS_RESET}"


def format_section(title: str) -> str:
    divider = f"{AETHOS_SLATE}{'─' * 44}{AETHOS_RESET}"
    return f"\n{divider}\n{AETHOS_BOLD}{AETHOS_PRIMARY}{title}{AETHOS_RESET}\n"


def format_status(label: str, value: str, *, tone: BrandTone = BrandTone.MUTED) -> str:
    color = _tone_color(tone)
    return f"  {AETHOS_SLATE}{label}:{AETHOS_RESET} {color}{value}{AETHOS_RESET}"


def format_banner(*, version: str = "0.2.0") -> str:
    lines = [
        "",
        f"{AETHOS_BOLD}{AETHOS_PRIMARY}  AethOS{AETHOS_RESET} {AETHOS_DIM}v{version}{AETHOS_RESET}",
        f"{AETHOS_SLATE}  Governed agentic operating system{AETHOS_RESET}",
        f"{AETHOS_SLATE}  Operational orchestration · evidence · audit{AETHOS_RESET}",
        "",
    ]
    return "\n".join(lines)


def strip_ansi(text: str) -> str:
    import re

    return re.sub(r"\033\[[0-9;]*m", "", text)
