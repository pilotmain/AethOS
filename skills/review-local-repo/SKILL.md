---
name: review-local-repo
description: Review the local repository — structure, recent changes, and risks — read-only.
---

## When to use

The operator asks for a code/repo review, "what changed", a risk read, or a
summary of the local project ("review this repo", "what's risky here").

## Steps

1. Map the repo (tree) and read the key entry points and changed files.
2. For "what changed", inspect recent commits / the working diff.
3. Report: structure, notable modules, recent changes, and concrete risks
   (untested paths, secrets, broken contracts) with file references.
4. Propose follow-ups (tests, fixes) as suggestions — implementing them is a
   separate explicit request.

## Readonly tools

- repo_tree / repo_read / repo_search

## Governance

Read-only review. Do not modify files; any edit is a separate explicit, governed
action. Never echo secrets found in the repo.
