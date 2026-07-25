# SPDX-License-Identifier: Apache-2.0
"""Hosted vs local JSON blob stores — shared tenant DB on hosted, file on local."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

_ROOT_KEY = "_root"


def use_hosted_shared_json_store() -> bool:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    return is_hosted_deployment()


def load_json_blob(
    namespace: str,
    file_path: Path,
    default_factory: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if use_hosted_shared_json_store():
        from aethos_core.tenancy.tenant_data_store import get_record

        data = get_record(namespace, _ROOT_KEY, default=None)
        return data if isinstance(data, dict) else default_factory()
    if not file_path.is_file():
        return default_factory()
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_factory()
    return data if isinstance(data, dict) else default_factory()


def save_json_blob(namespace: str, file_path: Path, data: dict[str, Any]) -> None:
    data = dict(data)
    data["updated_at"] = time.time()
    if use_hosted_shared_json_store():
        from aethos_core.tenancy.tenant_data_store import set_record

        set_record(namespace, _ROOT_KEY, data)
        return
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(file_path)


def clear_json_blob_for_tests(namespace: str, file_path: Path) -> None:
    if use_hosted_shared_json_store():
        from aethos_core.tenancy.tenant_data_store import clear_namespace

        clear_namespace(namespace)
        return
    if file_path.is_file():
        file_path.unlink()
