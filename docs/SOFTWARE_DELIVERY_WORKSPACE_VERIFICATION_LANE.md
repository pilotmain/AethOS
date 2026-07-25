# Software Delivery — Workspace Verification (FIX 125E)

**Governed verification** against the workspace tree after FIX 125D apply. No repo mutation, git, PR, deploy, dependency install, or arbitrary shell.

```text
… → apply workspace (125D) → verify workspace (125E) → PR draft (125F, gated)
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `run workspace verification` | Execute bounded checks + classify failures |
| `show workspace verification status` | Pass/fail + PR drafting gate |
| `show workspace verification report` | Full check output |

---

## Checks (125E)

| Check | Scope |
|-------|--------|
| Workspace tree inspection | Tree path exists under `workspaces/{plan_id}/tree/` |
| File existence | Applied files present in workspace |
| Static diff validation | Bounded 125C preview diffs (size / destructive pattern guards) |
| Workspace files modified | Workspace tree differs from repo for applied files |
| Python syntax | `ast.parse` on workspace `.py` files |
| Allowlisted test (optional) | Frozen `pytest_software_delivery_smoke` argv only |

Default: allowlisted pytest is **disabled** (`SOFTWARE_DELIVERY_WORKSPACE_ALLOW_ALLOWLISTED_TEST=false`).

---

## Failure classification

- `missing_workspace_file`
- `invalid_diff`
- `syntax_error`
- `allowlisted_test_failed`
- `verification_blocked`

---

## PR drafting gate (125F)

`PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E` — PR drafting is blocked until `status == passed` and `pr_drafting_unblocked == true`.

---

## Environment

```bash
SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_ENABLED=true
SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_REQUIRE_APPLIED=true
SOFTWARE_DELIVERY_WORKSPACE_ALLOW_ALLOWLISTED_TEST=false
```

---

## Related

- [SOFTWARE_DELIVERY_WORKSPACE_APPLICATION_LANE.md](./SOFTWARE_DELIVERY_WORKSPACE_APPLICATION_LANE.md)
