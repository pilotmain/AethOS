# GitHub Provider Operations Skill

Repository and workflow operations — readonly first.

## Supported operations

- workflows
- reruns (stub)
- checks
- PRs (readonly)
- commits (readonly)
- repo binding
- deployment source verification

## Required credentials

- GitHub token with repo/workflow scope

## Readonly tools

- list_workflows
- workflow_runs
- check_runs
- list_pull_requests

## Mutation tools

- rerun_workflow (not implemented)

## Evidence rules

- Tie workflow conclusions to commit SHA and run timestamps.

## Verification rules

- Deployment verification requires matching repo + workflow run success.

## Rollback rules

- Not implemented.

## Common failure patterns

- Token missing workflow scope
- Repo binding mismatch

## Repair recipes

- Reconcile repo binding, rerun readonly workflow inspection
