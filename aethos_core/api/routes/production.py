# SPDX-License-Identifier: Apache-2.0
"""Production API — deployment, cluster, edge."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["production"])


@router.get("/production/topology")
def production_topology_api() -> dict[str, Any]:
    from aethos_core.production.deployment_topology import get_deployment_topology

    return get_deployment_topology()


@router.get("/production/validate")
def production_validate_api() -> dict[str, Any]:
    from aethos_core.production.deployment_topology import validate_production_environment

    return validate_production_environment()


@router.get("/production/cluster")
def production_cluster_api() -> dict[str, Any]:
    from aethos_core.runtime.distributed.cluster_status import get_cluster_status

    return get_cluster_status()


@router.get("/production/edge")
def production_edge_api() -> dict[str, Any]:
    from aethos_core.runtime.edge_runtime import get_edge_runtime_status, get_hosted_cloud_status

    return {"edge": get_edge_runtime_status(), "hosted": get_hosted_cloud_status()}
