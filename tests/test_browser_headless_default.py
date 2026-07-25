# SPDX-License-Identifier: Apache-2.0
"""Browser capture must default to headless — hosted containers have no X server, so a
headed launch dies with 'Missing X server or $DISPLAY' and no screenshot is produced."""

from __future__ import annotations

from aethos_core.config import Settings


def test_browser_headless_defaults_true():
    assert Settings.model_fields["browser_headless"].default is True
