# SPDX-License-Identifier: Apache-2.0
"""FIX 335 — bounded generation plans for supported stacks."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    REQUIREMENT_TYPES,
    SUPPORTED_GENERATION_STACKS,
)

_TEMPLATE_STACK_MAP = {
    "fastapi_service": "python_fastapi",
    "spring_boot_service": "java_spring_boot",
    "nextjs_web_app": "nextjs",
    "fullstack_reference": "typescript",
    "generic_repository": "infrastructure_configuration",
}


def resolve_generation_stack(*, template_id: str | None, stack: str | None) -> str:
    if stack and stack in SUPPORTED_GENERATION_STACKS:
        return stack
    if template_id:
        mapped = _TEMPLATE_STACK_MAP.get(str(template_id).strip().lower())
        if mapped:
            return mapped
    return "infrastructure_configuration"


def build_generation_plan(*, request: dict[str, Any]) -> dict[str, Any]:
    feature = str(request.get("feature_name") or request.get("title") or "generated-feature")
    safe_feature = "".join(ch if ch.isalnum() else "-" for ch in feature).strip("-") or "generated-feature"
    stack = resolve_generation_stack(
        template_id=str(request.get("template_id") or ""),
        stack=str(request.get("stack") or ""),
    )
    req_type = str(request.get("requirement_type") or "task")
    if req_type not in REQUIREMENT_TYPES:
        req_type = "task"

    artifacts = _stack_artifacts(stack=stack, feature=safe_feature, request=request)
    files = [row["path"] for row in artifacts]
    modules = sorted({row["path"].split("/")[0] for row in artifacts if "/" in row["path"]})

    risk = "LOW"
    if req_type in {"bug", "enhancement"}:
        risk = "MEDIUM"
    if stack == "infrastructure_configuration" and req_type == "enhancement":
        risk = "MEDIUM"

    return {
        "plan_id": f"gen-plan-{safe_feature}",
        "feature_name": safe_feature,
        "requirement_type": req_type,
        "stack": stack,
        "files_affected": files,
        "modules_affected": modules,
        "dependencies_affected": _dependencies_for_stack(stack),
        "risk_level": risk,
        "artifacts": artifacts,
        "git_commit_performed": False,
        "read_only": True,
    }


def _dependencies_for_stack(stack: str) -> list[str]:
    mapping = {
        "java_spring_boot": ["spring-boot-starter-web", "spring-boot-starter-test"],
        "python_fastapi": ["fastapi", "pytest"],
        "nextjs": ["next", "react", "typescript"],
        "typescript": ["typescript", "vitest"],
        "infrastructure_configuration": ["github-actions"],
    }
    return mapping.get(stack, [])


def _stack_artifacts(*, stack: str, feature: str, request: dict[str, Any]) -> list[dict[str, Any]]:
    title = str(request.get("title") or feature.replace("-", " ").title())
    description = str(request.get("description") or request.get("content") or title)

    if stack == "python_fastapi":
        module = feature.replace("-", "_")
        return [
            {
                "path": f"app/routes/{module}.py",
                "kind": "code",
                "action": "create",
                "content": (
                    f'"""Generated route for {title}."""\n\n'
                    "from fastapi import APIRouter\n\n"
                    f"router = APIRouter(prefix='/{feature}', tags=['{feature}'])\n\n"
                    "@router.get('/')\n"
                    "def read_feature():\n"
                    f"    return {{'feature': '{feature}', 'status': 'generated'}}\n"
                ),
            },
            {
                "path": f"tests/test_{module}.py",
                "kind": "test",
                "action": "create",
                "content": (
                    f'"""Generated tests for {title}."""\n\n'
                    f"def test_{module}_placeholder():\n"
                    "    assert True\n",
                ),
            },
            {
                "path": f"docs/implementation-{feature}.md",
                "kind": "documentation",
                "action": "create",
                "content": (
                    f"# Implementation Notes — {title}\n\n"
                    f"{description}\n\n"
                    "Generated under EXECUTION_TRACK_2 human review.\n",
                ),
            },
            {
                "path": ".github/workflows/generated-validation.yml",
                "kind": "configuration",
                "action": "create",
                "content": (
                    "name: generated-validation\n"
                    "on: workflow_dispatch\n"
                    "jobs:\n"
                    "  validate:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - uses: actions/checkout@v4\n"
                    "      - run: echo 'Generated validation placeholder'\n"
                ),
            },
        ]

    if stack == "java_spring_boot":
        class_name = "".join(part.capitalize() for part in feature.split("-")) or "GeneratedFeature"
        package_path = "com/example/generated"
        return [
            {
                "path": f"src/main/java/{package_path.replace('.', '/')}/{class_name}Controller.java",
                "kind": "code",
                "action": "create",
                "content": (
                    f"package {package_path};\n\n"
                    "import org.springframework.web.bind.annotation.GetMapping;\n"
                    "import org.springframework.web.bind.annotation.RestController;\n\n"
                    "@RestController\n"
                    f"public class {class_name}Controller {{\n"
                    "    @GetMapping(\"/" + feature + "\")\n"
                    "    public String feature() {\n"
                    f"        return \"{feature}\";\n"
                    "    }\n"
                    "}\n",
                ),
            },
            {
                "path": f"src/test/java/{package_path.replace('.', '/')}/{class_name}Test.java",
                "kind": "test",
                "action": "create",
                "content": (
                    f"package {package_path};\n\n"
                    "import org.junit.jupiter.api.Test;\n"
                    "import static org.junit.jupiter.api.Assertions.assertTrue;\n\n"
                    f"class {class_name}Test {{\n"
                    "    @Test\n"
                    "    void generatedPlaceholder() {\n"
                    "        assertTrue(true);\n"
                    "    }\n"
                    "}\n",
                ),
            },
            {
                "path": f"docs/architecture-{feature}.md",
                "kind": "documentation",
                "action": "create",
                "content": f"# Architecture Notes — {title}\n\n{description}\n",
            },
        ]

    if stack == "nextjs":
        return [
            {
                "path": f"app/{feature}/page.tsx",
                "kind": "code",
                "action": "create",
                "content": (
                    f"export default function {feature.replace('-', '').title()}Page() {{\n"
                    "  return (\n"
                    "    <main>\n"
                    f"      <h1>{title}</h1>\n"
                    "    </main>\n"
                    "  );\n"
                    "}\n",
                ),
            },
            {
                "path": f"__tests__/{feature}.test.ts",
                "kind": "test",
                "action": "create",
                "content": (
                    f"describe('{title}', () => {{\n"
                    "  it('generated placeholder', () => {\n"
                    "    expect(true).toBe(true);\n"
                    "  });\n"
                    "});\n",
                ),
            },
            {
                "path": f"docs/implementation-{feature}.md",
                "kind": "documentation",
                "action": "create",
                "content": f"# Implementation Notes — {title}\n\n{description}\n",
            },
        ]

    if stack == "typescript":
        return [
            {
                "path": f"web/lib/{feature}.ts",
                "kind": "code",
                "action": "create",
                "content": (
                    f"export function {feature.replace('-', '_')}() {{\n"
                    f"  return '{feature}';\n"
                    "}\n",
                ),
            },
            {
                "path": f"api/app/routes/{feature.replace('-', '_')}.py",
                "kind": "code",
                "action": "create",
                "content": (
                    f'"""Generated API route for {title}."""\n\n'
                    "def handler():\n"
                    f"    return {{'feature': '{feature}'}}\n",
                ),
            },
            {
                "path": f"web/__tests__/{feature}.test.ts",
                "kind": "test",
                "action": "create",
                "content": (
                    f"import {{ {feature.replace('-', '_')} }} from '../lib/{feature}';\n\n"
                    "test('generated placeholder', () => {\n"
                    f"  expect({feature.replace('-', '_')}()).toBe('{feature}');\n"
                    "});\n",
                ),
            },
            {
                "path": f"docs/implementation-{feature}.md",
                "kind": "documentation",
                "action": "create",
                "content": f"# Implementation Notes — {title}\n\n{description}\n",
            },
        ]

    return [
        {
            "path": f"src/{feature}.md",
            "kind": "documentation",
            "action": "create",
            "content": f"# {title}\n\n{description}\n",
        },
        {
            "path": "aethos/generation-metadata.json",
            "kind": "configuration",
            "action": "create",
            "content": json.dumps(
                {
                    "feature": feature,
                    "stack": stack,
                    "generation_track": "EXECUTION_TRACK_2",
                    "git_commit_performed": False,
                },
                indent=2,
            )
            + "\n",
        },
        {
            "path": f"tests/test_{feature.replace('-', '_')}.py",
            "kind": "test",
            "action": "create",
            "content": f"def test_{feature.replace('-', '_')}():\n    assert True\n",
        },
    ]
