# SPDX-License-Identifier: Apache-2.0
"""Vercel mutation adapter — governed redeploy and env var mutations."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.base.mutation_adapter import MutationAdapter, MutationNotEnabledError
from aethos_core.providers.vercel.auth import VercelAuthAdapter
from aethos_core.providers.vercel.operations.deploy_mutations_api import deploy_from_git, promote_deployment, rollback
from aethos_core.providers.vercel.operations.mutations_api import redeploy_project, remove_env_var, stop_project, upsert_env_var


class VercelMutationAdapter(MutationAdapter):
    provider = "vercel"

    @property
    def enabled(self) -> bool:
        return get_settings().mutation_execution_enabled and get_settings().mutation_t3_production_enabled

    def supported_mutations(self) -> list[str]:
        ops = ["redeploy", "stop", "restart", "rollback", "promote_deployment", "deploy_from_git"]
        if get_settings().provider_env_var_mutations_enabled:
            ops.extend(["set_env_var", "remove_env_var"])
        return ops

    def dry_run(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        target = str(params.get("target_name") or "(unknown)")
        env_name = str(params.get("env_var_name") or params.get("env_key") or "")
        if operation == "rollback":
            detail = f"Would roll back `{target}` to its previous production deployment — no mutation performed."
        elif operation == "promote_deployment":
            dep = str(params.get("deployment_id") or "(deployment id required)")
            detail = f"Would promote deployment `{dep}` to production for `{target}` — no mutation performed."
        elif operation == "deploy_from_git":
            ref = str(params.get("ref") or "the default branch")
            detail = f"Would trigger a production deployment of `{target}` from git (`{ref}`) — no mutation performed."
        elif operation == "restart":
            detail = f"Would restart Vercel project `{target}` by redeploying its current production deployment — no mutation performed."
        elif operation == "set_env_var":
            detail = f"Would upsert env var `{env_name or '(name required)'}` on `{target}` — no mutation performed."
        elif operation == "remove_env_var":
            detail = f"Would remove env var `{env_name or '(name required)'}` from `{target}` — no mutation performed."
        elif operation == "stop":
            detail = f"Would stop Vercel project `{target}` (cancel in-flight build or pause live production) — no mutation performed."
        else:
            detail = f"Would redeploy Vercel project `{target}` — no mutation performed."
        return {
            "ok": True,
            "dry_run": True,
            "operation": operation,
            "target_name": target,
            "detail": detail,
        }

    def execute(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        self.assert_enabled()
        if operation not in self.supported_mutations():
            raise MutationNotEnabledError(f"Unsupported Vercel mutation: {operation}")
        credential_id = str(params.get("credential_id") or "")
        if not credential_id:
            return {"ok": False, "detail": "Vercel credential not configured for mutation execution."}
        token = VercelAuthAdapter().get_api_token(credential_id)
        target = str(params.get("target_name") or "")
        if not target:
            return {"ok": False, "detail": "Target project name required."}
        team_id_opt = str(params.get("vercel_team_id") or get_settings().vercel_team_id or "").strip() or None
        if operation == "rollback":
            return rollback(token, target_name=target, team_id=team_id_opt)
        if operation == "promote_deployment":
            return promote_deployment(
                token, target_name=target, deployment_id=str(params.get("deployment_id") or ""), team_id=team_id_opt
            )
        if operation == "deploy_from_git":
            return deploy_from_git(
                token, target_name=target, ref=(str(params.get("ref")) if params.get("ref") else None), team_id=team_id_opt
            )
        if operation == "set_env_var":
            key = str(params.get("env_var_name") or params.get("env_key") or "")
            value = str(params.get("env_var_value") or "")
            if not value and isinstance(params.get("env_var_reference"), dict):
                value = str(params.get("env_var_value") or "")
            if not key or not value:
                return {"ok": False, "detail": "Env var name and value required (via secure preflight reference)."}
            return upsert_env_var(token, target_name=target, key=key, value=value)
        if operation == "remove_env_var":
            key = str(params.get("env_var_name") or params.get("env_key") or "")
            if not key:
                return {"ok": False, "detail": "Env var key required for removal."}
            return remove_env_var(token, target_name=target, key=key)
        if operation == "stop":
            team_id = str(params.get("vercel_team_id") or get_settings().vercel_team_id or "").strip() or None
            vercel_target = str(params.get("vercel_project") or params.get("target_name") or target).strip()
            return stop_project(token, target_name=vercel_target or target, team_id=team_id)
        # Serverless has no "restart" — restarting a Vercel project means redeploying its
        # current production deployment. Honest alias to the real redeploy executor.
        team_id = str(params.get("vercel_team_id") or get_settings().vercel_team_id or "").strip() or None
        result = redeploy_project(token, target_name=target, team_id=team_id)
        if operation == "restart" and isinstance(result, dict):
            result.setdefault("operation", "restart")
        return result
