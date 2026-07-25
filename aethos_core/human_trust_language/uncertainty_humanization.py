# SPDX-License-Identifier: Apache-2.0
"""Uncertainty humanization — graceful uncertainty."""

from __future__ import annotations

from aethos_core.human_trust.uncertainty_narratives import uncertainty_narrative


def humanize_uncertainty(*, confidence: float) -> str:
    return uncertainty_narrative(confidence=confidence)
