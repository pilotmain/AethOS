# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — local-first productivity surfaces (handoff §8).

Each tab is gated by WORKSPACE_SUITE_ENABLED. Read-only and draft-only features run
inline; anything that sends, publishes, or mutates goes through a governed
preflight → approve step. Local-first: the operator's data on the operator's
hardware, stored as gitignored JSON under the workspace-suite store dir.
"""
