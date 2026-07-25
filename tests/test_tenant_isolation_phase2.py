# SPDX-License-Identifier: Apache-2.0
"""Two-tenant isolation harness (grows alongside each phase, per Correction 5).

Phase 2: credential invisibility, revoke scope, no cross-tenant key fallback,
per-tenant preferred method, per-tenant arbiter rate limits.

Phase 3: runtime config independence, singleton not polluted by other tenants,
per-tenant model selection.

Phase 4: deployment-operator governance gates, per-tenant org isolation, RBAC in
shared mode.

Phase 5: DB-row-level data isolation — conversation threads/goals, operational memory,
conversation summary memory, vector memory, agent artifacts.

Phase 6 release gate (Correction 5): composite harness proving credential invisibility,
config independence, data isolation, and governance denial in one pass.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.tenancy import tenant_scope


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "creds"))
    monkeypatch.setenv("RUNTIME_CONFIG_DIR", str(tmp_path / "runtime_config"))
    monkeypatch.setenv("TENANT_DATA_DIR", str(tmp_path / "tenant_data"))
    monkeypatch.setenv("CONVERSATION_MEMORY_DIR", str(tmp_path / "conversation_memory"))
    monkeypatch.setenv("ARBITER_ENABLED", "false")
    get_settings.cache_clear()
    from aethos_core.memory import conversation_summary_memory as conv_mem
    from aethos_core.runtime_config import runtime_config_store as config_store
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests
    from aethos_core.tenancy import tenant_limits
    from aethos_core.tenancy.tenant_data_store import reset_for_tests as reset_tenant_data

    from aethos_core.orgs.organizations import clear_orgs_for_tests

    reset_credential_vault_for_tests()
    config_store.reset_for_tests()
    tenant_limits.reset_for_tests()
    reset_tenant_data()
    conv_mem.reset_for_tests()
    clear_orgs_for_tests()
    yield
    reset_credential_vault_for_tests()
    config_store.reset_for_tests()
    tenant_limits.reset_for_tests()
    reset_tenant_data()
    conv_mem.reset_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def _vault():
    from aethos_core.security.credential_vault import get_credential_vault

    return get_credential_vault()


def _enable_multi_tenant(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()


# ───────────────────────── credential invisibility ───────────────────────────


def test_credentials_invisible_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    vault = _vault()

    with tenant_scope("alice@example.com"):
        rec_a = vault.store_api_token(provider="openai", label="A key", token="sk-alice-123")
    with tenant_scope("bob@example.com"):
        rec_b = vault.store_api_token(provider="openai", label="B key", token="sk-bob-456")

    # Each tenant sees only their own credential.
    with tenant_scope("alice@example.com"):
        ids = [r.credential_id for r in vault.list_credentials()]
        assert ids == [rec_a.credential_id]
        # Bob's credential is invisible: no metadata, no secret.
        assert vault.get(rec_b.credential_id) is None
        assert vault.retrieve_secret(rec_b.credential_id) is None
        # Own secret is retrievable.
        assert vault.retrieve_secret(rec_a.credential_id) == {"token": "sk-alice-123"}

    with tenant_scope("bob@example.com"):
        ids = [r.credential_id for r in vault.list_credentials()]
        assert ids == [rec_b.credential_id]
        assert vault.get(rec_a.credential_id) is None
        assert vault.retrieve_secret(rec_a.credential_id) is None


def test_revoke_is_owner_scoped(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    vault = _vault()

    with tenant_scope("alice@example.com"):
        rec_a = vault.store_api_token(provider="openai", label="A", token="sk-alice")
    with tenant_scope("bob@example.com"):
        rec_b = vault.store_api_token(provider="openai", label="B", token="sk-bob")

    # Bob cannot revoke Alice's credential.
    with tenant_scope("bob@example.com"):
        assert vault.revoke(rec_a.credential_id) is False
        # Bob revoking his own works.
        assert vault.revoke(rec_b.credential_id) is True

    # Alice's credential is untouched.
    with tenant_scope("alice@example.com"):
        assert vault.get(rec_a.credential_id) is not None
        assert vault.retrieve_secret(rec_a.credential_id) == {"token": "sk-alice"}


def test_preferred_method_is_per_tenant(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    vault = _vault()
    with tenant_scope("alice@example.com"):
        vault.set_preferred_method("openai", "api_token")
        assert vault.get_preferred_method("openai") == "api_token"
    with tenant_scope("bob@example.com"):
        assert vault.get_preferred_method("openai") == "ask"


# ───────────────────── key resolution: no cross-tenant fallback ───────────────


def test_resolve_key_no_cross_tenant_and_env_is_operator_only(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    # Operator's deployment .env key for OpenAI.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-operator-env")
    get_settings.cache_clear()

    from aethos_core.llm.model_providers import resolve_model_provider_key

    vault = _vault()
    with tenant_scope("alice@example.com"):
        vault.store_api_token(provider="openai", label="A", token="sk-alice-byok")

    # Alice resolves her own vault key (not the operator env key).
    with tenant_scope("alice@example.com"):
        assert resolve_model_provider_key("openai") == "sk-alice-byok"

    # Bob has no key and is a non-operator tenant ⇒ no env fallback ⇒ empty.
    with tenant_scope("bob@example.com"):
        assert resolve_model_provider_key("openai") == ""

    # The operator/default tenant may use the deployment env key.
    from aethos_core.tenancy import DEFAULT_TENANT

    with tenant_scope(DEFAULT_TENANT):
        assert resolve_model_provider_key("openai") == "sk-operator-env"


# ─────────────────────────── per-tenant rate limits ──────────────────────────


def test_arbiter_rate_limit_is_per_tenant(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("TENANT_ARBITER_RUNS_PER_HOUR", "2")
    get_settings.cache_clear()
    from aethos_core.tenancy.tenant_limits import check_arbiter_run

    # Alice: allowed twice, blocked on the third.
    assert check_arbiter_run("alice@example.com")[0] is True
    assert check_arbiter_run("alice@example.com")[0] is True
    allowed, retry_after = check_arbiter_run("alice@example.com")
    assert allowed is False and retry_after > 0

    # Bob is unaffected by Alice's usage.
    assert check_arbiter_run("bob@example.com")[0] is True

    # Operator/default tenant is exempt.
    from aethos_core.tenancy import DEFAULT_TENANT

    for _ in range(5):
        assert check_arbiter_run(DEFAULT_TENANT)[0] is True


def test_arbiter_rate_limit_noop_when_single_tenant(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    monkeypatch.setenv("TENANT_ARBITER_RUNS_PER_HOUR", "1")
    get_settings.cache_clear()
    from aethos_core.tenancy.tenant_limits import check_arbiter_run

    for _ in range(5):
        assert check_arbiter_run("alice@example.com")[0] is True


# ───────────────────────── flag OFF: unchanged behavior ───────────────────────


# ───────────────────── Phase 3: runtime config independence ──────────────────


def test_runtime_config_independent_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.runtime_config.effective_settings import (
        effective_bool,
        set_effective_setting,
    )

    with tenant_scope("alice@example.com"):
        set_effective_setting("ARBITER_ENABLED", True, actor="alice@example.com")
        assert effective_bool("ARBITER_ENABLED") is True

    with tenant_scope("bob@example.com"):
        assert effective_bool("ARBITER_ENABLED") is False


def test_singleton_not_polluted_by_other_tenant(monkeypatch):
    """Alice's UI write must not mutate the global Settings singleton in MT mode."""
    _enable_multi_tenant(monkeypatch)
    from aethos_core import config as config_mod
    from aethos_core.runtime_config.effective_settings import set_effective_setting

    assert config_mod.get_settings().arbiter_enabled is False
    with tenant_scope("alice@example.com"):
        set_effective_setting("ARBITER_ENABLED", True, actor="alice@example.com")
    assert config_mod.get_settings().arbiter_enabled is False


def test_model_selection_independent_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.llm.model_providers import model_provider_spec
    from aethos_core.llm.model_selection import (
        enabled_models_for_provider,
        set_provider_model_selection,
    )

    spec = model_provider_spec("deepseek")
    with tenant_scope("alice@example.com"):
        set_provider_model_selection(
            "deepseek",
            enabled_ids=["deepseek-chat"],
            custom_ids=[],
            actor="alice@example.com",
        )
        alice_ids = [m for m, _ in enabled_models_for_provider(spec)]
        assert "deepseek-reasoner" not in alice_ids

    with tenant_scope("bob@example.com"):
        bob_ids = [m for m, _ in enabled_models_for_provider(spec)]
        assert "deepseek-reasoner" in bob_ids


def test_arbiter_pool_reads_tenant_config(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.arbiter import pool as pool_mod
    from aethos_core.runtime_config.effective_settings import effective_str, set_effective_setting

    pool_str = "anthropic:claude-sonnet-4-6,openrouter:openai/gpt-4.1-mini"
    with tenant_scope("alice@example.com"):
        set_effective_setting("ARBITER_MODEL_POOL", pool_str, actor="alice@example.com")
        assert {e["provider"] for e in pool_mod.parse_model_pool()} == {"anthropic", "openrouter"}

    with tenant_scope("bob@example.com"):
        assert effective_str("ARBITER_MODEL_POOL") == ""


# ─────────────────── Phase 4: operator vs tenant separation ─────────────────


def test_orgs_isolated_per_tenant(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.orgs.organizations import get_current_organization
    from aethos_core.orgs.tenant_bridge import org_id_for_tenant

    with tenant_scope("alice@example.com"):
        alice_org = get_current_organization()
    with tenant_scope("bob@example.com"):
        bob_org = get_current_organization()

    assert alice_org["org_id"] == org_id_for_tenant("alice@example.com")
    assert bob_org["org_id"] == org_id_for_tenant("bob@example.com")
    assert alice_org["org_id"] != bob_org["org_id"]
    assert alice_org.get("tenant_id") == "alice@example.com"
    assert bob_org.get("tenant_id") == "bob@example.com"


def test_governance_override_rejected_for_tenant_operator(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.governance.governance_override_store import save_governance_override
    from aethos_core.tenancy.operator import is_deployment_operator

    operator_user = {"email": "alice@example.com", "roles": ["operator"]}
    admin_user = {"email": "admin@example.com", "roles": ["admin"]}
    assert is_deployment_operator(operator_user) is False
    assert is_deployment_operator(admin_user) is True

    with pytest.raises(PermissionError):
        save_governance_override(
            key="mutation_execution_enabled",
            value=True,
            user=operator_user,
        )


def test_governance_diagnostics_blocked_for_non_admin_in_mt_mode(monkeypatch, tmp_path):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import aethos_core.api.routes.aethos_identity as ident
    from aethos_core.api.routes import governance_diagnostics
    from aethos_core.security import rbac
    from aethos_core.tenancy.middleware import tenant_context_middleware

    app = FastAPI()
    app.middleware("http")(tenant_context_middleware)
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")
    app.include_router(governance_diagnostics.router, prefix="/api/v1")

    client = TestClient(app)
    client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    )
    import json

    store = json.loads(ident._store_path().read_text())
    store["users"]["op@aethos.test"] = {
        "user_id": "op@aethos.test",
        "email": "op@aethos.test",
        "roles": ["operator"],
        "auth": "local",
        "password": ident.hash_password("operatorpass12"),
    }
    ident._save_store(store)

    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "op@aethos.test", "password": "operatorpass12"},
    )
    resp = client.get("/api/v1/governance/diagnostics")
    assert resp.status_code == 403
    assert resp.json().get("detail") == "deployment_operator_required"


# ─────────────── Phase 5: per-tenant data isolation (Correction 2) ────────────


def test_conversation_threads_isolated_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.conversation.conversation_runtime import (
        get_conversational_goal,
        record_conversation_thread,
        set_conversational_goal,
    )
    from aethos_core.tenancy.tenant_data_store import get_record

    sid = "shared-session"
    with tenant_scope("alice@example.com"):
        record_conversation_thread(session_id=sid, topics=["alice-topic"], summary="alice recap")
        set_conversational_goal(session_id=sid, goal="alice goal", steps=["a1"])

    with tenant_scope("bob@example.com"):
        threads = get_record("conversation_threads", sid, default=[])
        goal = get_conversational_goal(session_id=sid)
        assert threads == []
        assert goal == {}

    with tenant_scope("alice@example.com"):
        threads = get_record("conversation_threads", sid, default=[])
        assert len(threads) == 1
        assert threads[0]["topics"] == ["alice-topic"]
        assert get_conversational_goal(session_id=sid).get("goal") == "alice goal"


def test_operational_memory_isolated_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.conversation.operational_memory import (
        load_operational_memory,
        record_focus_recovery,
        track_unresolved_issue,
    )

    sid = "ops-session"
    with tenant_scope("alice@example.com"):
        record_focus_recovery(session_id=sid, focus="alice-focus")
        track_unresolved_issue(session_id=sid, issue="alice-blocker")

    with tenant_scope("bob@example.com"):
        mem = load_operational_memory(session_id=sid)
        assert mem.get("last_focus") is None
        assert mem.get("unresolved_issues") == []

    with tenant_scope("alice@example.com"):
        mem = load_operational_memory(session_id=sid)
        assert mem.get("last_focus") == "alice-focus"
        assert "alice-blocker" in (mem.get("unresolved_issues") or [])


def test_conversation_summary_isolated_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.memory.conversation_summary_memory import (
        compose_conversation_recap_text,
        get_session_summary,
        record_turn,
    )

    sid = "summary-session"
    with tenant_scope("alice@example.com"):
        record_turn(session_id=sid, user_text="alice asked about deploy", reply="alice reply", intent="chat")
        alice_summary = get_session_summary(sid)

    with tenant_scope("bob@example.com"):
        assert get_session_summary(sid).get("summary", "") == ""
        assert compose_conversation_recap_text(sid) is None

    with tenant_scope("alice@example.com"):
        assert "alice asked" in (alice_summary.get("summary") or "")


def test_vector_memory_isolated_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    get_settings.cache_clear()
    from aethos_core.memory.vector_store import recall, remember

    with tenant_scope("alice@example.com"):
        remember(text="alice secret operational fact about billing", tags=["alice"])
    with tenant_scope("bob@example.com"):
        remember(text="bob unrelated fact about weather", tags=["bob"])

    with tenant_scope("bob@example.com"):
        matches = recall(query="alice secret billing", limit=5).get("matches") or []
        texts = [str(m.get("text") or "") for m in matches]
        assert not any("alice secret" in t for t in texts)

    with tenant_scope("alice@example.com"):
        matches = recall(query="alice secret billing", limit=5).get("matches") or []
        texts = [str(m.get("text") or "") for m in matches]
        assert any("alice secret" in t for t in texts)


def test_agent_artifacts_isolated_across_tenants(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.agents.runtime.artifacts import (
        get_agent_artifact,
        list_agent_artifacts,
        store_agent_artifact,
    )

    with tenant_scope("alice@example.com"):
        rec = store_agent_artifact(
            artifact_type="agent_evidence",
            agent_id="agent-a",
            plan_id="plan-a",
            payload={"note": "alice evidence"},
            summary="alice artifact",
        )
        alice_id = rec["artifact_id"]

    with tenant_scope("bob@example.com"):
        assert get_agent_artifact(alice_id) is None
        assert all(a.get("artifact_id") != alice_id for a in list_agent_artifacts())

    with tenant_scope("alice@example.com"):
        loaded = get_agent_artifact(alice_id)
        assert loaded is not None
        assert loaded.get("payload", {}).get("note") == "alice evidence"


# ───────────── Correction 5 release gate (composite isolation harness) ─────


def test_release_gate_composite_two_tenant_isolation(monkeypatch):
    """Blocking gate before any public MULTI_TENANT_ENABLED URL — one harness, all pillars."""
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-operator-env")
    get_settings.cache_clear()
    vault = _vault()
    from aethos_core.llm.model_providers import resolve_model_provider_key
    from aethos_core.memory.vector_store import recall, remember
    from aethos_core.runtime_config.effective_settings import effective_bool, set_effective_setting
    from aethos_core.tenancy.tenant_data_store import get_record

    # (a) Credential invisibility + no env fallback for tenants
    with tenant_scope("alice@example.com"):
        rec_a = vault.store_api_token(provider="openai", label="A", token="sk-alice-gate-key")
    with tenant_scope("bob@example.com"):
        assert vault.get(rec_a.credential_id) is None
        assert resolve_model_provider_key("openai") == ""

    # (b) Config independence
    with tenant_scope("alice@example.com"):
        set_effective_setting("ARBITER_ENABLED", True, actor="alice@example.com")
    with tenant_scope("bob@example.com"):
        assert effective_bool("ARBITER_ENABLED") is False

    # (c) Data-row isolation (vector memory spot-check)
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    get_settings.cache_clear()
    with tenant_scope("alice@example.com"):
        remember(text="alice release-gate secret", tags=["gate"])
    with tenant_scope("bob@example.com"):
        matches = recall(query="alice release-gate", limit=5).get("matches") or []
        assert not any("alice release-gate" in str(m.get("text") or "") for m in matches)

    # (d) Governance denial for tenant operator
    from aethos_core.governance.governance_override_store import save_governance_override

    with pytest.raises(PermissionError):
        save_governance_override(
            key="mutation_execution_enabled",
            value=True,
            user={"email": "alice@example.com", "roles": ["operator"]},
        )

    # Conversation thread isolation spot-check
    from aethos_core.conversation.conversation_runtime import record_conversation_thread

    with tenant_scope("alice@example.com"):
        record_conversation_thread(session_id="gate", topics=["alice-only"], summary="gate")
    with tenant_scope("bob@example.com"):
        assert get_record("conversation_threads", "gate", default=[]) == []


# ───────────────────────── chat agent detached tenant ─────────────────────────


def test_chat_agent_resolves_provider_token_in_detached_worker(monkeypatch):
    """Correction 1 — chat streaming worker threads must carry the originating tenant."""
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("RAILWAY_TOKEN", "")
    monkeypatch.setenv("RAILWAY_API_TOKEN", "")
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "railway_api_token", "")
    vault = _vault()

    with tenant_scope("alice@example.com"):
        vault.store_api_token(provider="railway", label="alice-r", token="railway-token-alice")
    with tenant_scope("bob@example.com"):
        vault.store_api_token(provider="railway", label="bob-r", token="railway-token-bob")

    import threading

    from aethos_core.chat.chat_turn_tenant import chat_turn_scope
    from aethos_core.execution_brain.cloud_agent_bridge import resolve_provider_token

    alice_holder: dict[str, str | None] = {}
    bob_holder: dict[str, str | None] = {}
    stranger_holder: dict[str, str | None] = {}

    def alice_worker() -> None:
        with chat_turn_scope("alice@example.com"):
            token, _ = resolve_provider_token("railway", require_validated=False)
            alice_holder["token"] = token

    def bob_worker() -> None:
        with chat_turn_scope("bob@example.com"):
            token, _ = resolve_provider_token("railway", require_validated=False)
            bob_holder["token"] = token

    def stranger_worker() -> None:
        with chat_turn_scope("stranger@example.com"):
            token, _ = resolve_provider_token("railway", require_validated=False)
            stranger_holder["token"] = token

    threads = [
        threading.Thread(target=alice_worker),
        threading.Thread(target=bob_worker),
        threading.Thread(target=stranger_worker),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert alice_holder.get("token") == "railway-token-alice"
    assert bob_holder.get("token") == "railway-token-bob"
    assert stranger_holder.get("token") is None


def test_provider_inventory_all_thread_pool_keeps_tenant(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("RAILWAY_TOKEN", "")
    monkeypatch.setenv("RAILWAY_API_TOKEN", "")
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "railway_api_token", "")
    vault = _vault()

    with tenant_scope("alice@example.com"):
        vault.store_api_token(provider="railway", label="alice-r", token="railway-token-alice")

    import json
    import threading

    from aethos_core.chat.chat_turn_tenant import chat_turn_scope
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    alice_ok: dict[str, bool] = {}
    stranger_ok: dict[str, bool] = {}

    def alice_worker() -> None:
        with chat_turn_scope("alice@example.com"):
            raw = execute_agent_tool("provider_inventory_all", {"mode": "quick", "limit": 50})
            rows = json.loads(raw).get("providers") or []
            railway = next((r for r in rows if r.get("provider") == "railway"), {})
            alice_ok["railway"] = bool(railway.get("connection_ok"))

    def stranger_worker() -> None:
        with chat_turn_scope("stranger@example.com"):
            raw = execute_agent_tool("provider_inventory_all", {"mode": "quick", "limit": 50})
            rows = json.loads(raw).get("providers") or []
            railway = next((r for r in rows if r.get("provider") == "railway"), {})
            stranger_ok["railway"] = bool(railway.get("connection_ok"))

    t1 = threading.Thread(target=alice_worker)
    t2 = threading.Thread(target=stranger_worker)
    t1.start()
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)

    assert alice_ok.get("railway") is True
    assert stranger_ok.get("railway") is False


# ───────────────────────── flag OFF: unchanged behavior ───────────────────────


def test_single_tenant_ignores_ambient_tenant(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    get_settings.cache_clear()
    vault = _vault()

    # Even if some ambient scope is set, single-tenant mode owns everything as
    # "default" and reads are unaffected.
    with tenant_scope("someone@example.com"):
        rec = vault.store_api_token(provider="openai", label="op", token="sk-op")
    # A different ambient scope still sees it (single global owner).
    with tenant_scope("another@example.com"):
        assert vault.get(rec.credential_id) is not None
        assert vault.retrieve_secret(rec.credential_id) == {"token": "sk-op"}
    assert vault.list_credentials()[0].credential_id == rec.credential_id
