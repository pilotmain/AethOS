# SPDX-License-Identifier: Apache-2.0
"""Cold start — heavy API routers lazy-mounted after /health (Part A §A3)."""

from __future__ import annotations

import importlib
import sys


def test_heavy_mission_control_router_not_imported_at_main_load():
    """Eager boot mounts light routers only; mission_control is deferred."""
    to_drop = [k for k in sys.modules if k.startswith("aethos_core.api")]
    for key in to_drop:
        sys.modules.pop(key, None)

    import aethos_core.api.main as main_mod  # noqa: WPS433

    importlib.reload(main_mod)
    assert "aethos_core.api.routes.mission_control" not in sys.modules
