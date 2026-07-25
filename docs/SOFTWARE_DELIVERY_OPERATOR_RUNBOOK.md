# Software delivery operator runbook

AethOS can prepare repository changes through a governed sequence:

```text
issue/context -> plan -> branch -> patch proposal -> workspace apply
              -> verification -> pull-request preflight -> push -> open PR
```

## Before starting

- Register or select the intended repository and workspace.
- Confirm the GitHub credential has only the required repository permissions.
- Start from a clean worktree or explicitly account for existing changes.
- Use a feature branch; never target the protected default branch directly.
- Review the exact issue, requested scope, and excluded work.

## Governed sequence

1. Analyze the issue or request and create an implementation plan.
2. Review and approve the plan.
3. Create a feature branch.
4. Generate and review a bounded patch proposal.
5. Approve application to the governed workspace.
6. Run workspace verification and inspect failures.
7. Prepare a pull-request draft and GitHub preflight.
8. Review the branch-push preview and approve the push.
9. Review the pull-request preview and approve opening the PR.
10. Complete human code review on GitHub.

Each approval is scoped to its current preflight. A planning approval does not
authorize a workspace change, push, merge, deployment, or unrelated mutation.

## Required evidence

Before push or pull-request creation, confirm:

- the diff contains only intended files;
- tests and checks passed, with commands recorded;
- no credentials, personal data, runtime artifacts, or generated secrets appear;
- documentation and migration notes are current;
- rollback consists of a bounded revert or restoring the pre-apply snapshot;
- the target remote, repository, and branch are correct.

## Recovery

- If patch application is wrong, stop and use the governed workspace rollback.
- If verification fails, fix or rollback before creating a PR preflight.
- If GitHub authentication or scope fails, repair the credential and rerun the
  preflight; do not switch to an unreviewed direct push.
- If the protected branch is selected, create a feature branch and regenerate the
  delivery preflight.
- Treat an idempotent/replay response as a reason to inspect existing receipts,
  not to repeat the mutation.

Detailed runtime state definitions are documented in
[SOFTWARE_DELIVERY_PHASE_2_INDEX.md](SOFTWARE_DELIVERY_PHASE_2_INDEX.md).
