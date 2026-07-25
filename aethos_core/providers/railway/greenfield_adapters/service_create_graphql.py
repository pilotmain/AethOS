# SPDX-License-Identifier: Apache-2.0
"""Railway serviceCreate GraphQL — isolated from dry-run and simulation paths."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import graphql_query
from aethos_core.security.secret_redaction import redact_text

SERVICE_CREATE_MUTATION = """
mutation serviceCreate($input: ServiceCreateInput!) {
  serviceCreate(input: $input) {
    id
    name
  }
}
"""


def invoke_service_create(
    token: str,
    *,
    project_id: str,
    service_name: str,
    environment_id: str = "",
) -> dict[str, Any]:
    """
    Create an empty Railway service (no repo source, no env writes, no deploy).

    Never pass source.repo — GitHub connection is a later governed phase (FIX 111).
    """
    input_payload: dict[str, str] = {
        "projectId": project_id,
        "name": service_name,
    }
    if environment_id:
        input_payload["environmentId"] = environment_id

    out = graphql_query(token, SERVICE_CREATE_MUTATION, {"input": input_payload})
    if not out.get("ok"):
        errors = out.get("errors") or []
        detail = "; ".join(redact_text(str(item)) for item in errors) if errors else "serviceCreate failed"
        return {"ok": False, "detail": detail, "data": out.get("data")}

    node = ((out.get("data") or {}).get("serviceCreate")) or {}
    service_id = str(node.get("id") or "").strip()
    name = str(node.get("name") or service_name).strip()
    if not service_id:
        return {"ok": False, "detail": "serviceCreate returned no service id", "data": out.get("data")}
    return {
        "ok": True,
        "service_id": service_id,
        "service_name": name,
        "detail": "serviceCreate succeeded",
        "data": out.get("data"),
    }
