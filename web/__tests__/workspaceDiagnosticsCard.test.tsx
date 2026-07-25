import { describe, expect, it } from "vitest";

/** Settings payload shape for Mission Control workspace card. */
function workspaceFields(ws: {
  workspace_root?: string;
  runtime_python?: string;
  profile_store_path?: string;
}) {
  return [ws.workspace_root, ws.runtime_python, ws.profile_store_path].filter(Boolean).join("|");
}

describe("workspaceDiagnosticsCard", () => {
  it("expects canonical AethOS paths in settings workspace payload", () => {
    const payload = workspaceFields({
      workspace_root: "/Users/raya/AethOS",
      runtime_python: "/Users/raya/AethOS/.venv/bin/python3",
      profile_store_path: "/Users/raya/AethOS/data/browser_profiles",
    });
    expect(payload).toContain("/Users/raya/AethOS");
    expect(payload).toContain("browser_profiles");
    expect(payload).not.toContain("/Users/raya/aethos");
  });
});
