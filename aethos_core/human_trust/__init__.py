# SPDX-License-Identifier: Apache-2.0
"""Human trust — confidence restraint and human-readable phrasing."""

from aethos_core.human_trust.confidence_restraint import should_show_telemetry
from aethos_core.human_trust.confidence_language import human_confidence_phrase

__all__ = ["should_show_telemetry", "human_confidence_phrase"]
