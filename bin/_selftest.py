#!/usr/bin/env python3
"""pos-selftest orchestrator.

End-to-end selftest of the pos plugin: generates a synthetic project via
`npx tsx generator/run.ts --profile questionnaire/profiles/cli-tool.yaml`
and exercises the functional-critical gates against it.

Scope (ratified in F3 Fase -1):
- D1 pre-branch-gate (deny without marker)
- D3 pre-write-guard (deny write without test pair)
- D4 pre-pr-gate (deny PR with docs-sync missing)
- D5 post-action (confirmed merge emits /pos:compound suggestion)
- D6 stop-policy-check (allow/deny skill allowlist)

Out of scope: D2 session-start + D6 pre-compact (informative-only),
Claude Code runtime invocations, real skill/agent dispatch.

Stdlib only. No third-party deps.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "generator" / "run.ts"
PROFILE = REPO_ROOT / "questionnaire" / "profiles" / "cli-tool.yaml"
HOOKS_DIR = REPO_ROOT / "hooks"


def generate_synthetic(target: Path) -> None:
    """Generate synthetic project at `target` via `npx tsx generator/run.ts`.

    Generator refuses non-empty `--out`; caller passes a fresh path.
    """
    subprocess.run(
        [
            "npx", "tsx", str(GENERATOR),
            "--profile", str(PROFILE),
            "--out", str(target),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def invoke_hook(name: str, payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    """Invoke `hooks/<name>.py` from the meta-repo against `cwd`."""
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / f"{name}.py")],
        input=json.dumps(payload),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )


def scenario_d1_pre_branch_gate(synthetic: Path) -> tuple[bool, str]:
    """D1: deny `git checkout -b` without marker; allow with marker present."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git checkout -b feat/example"},
    }

    res = invoke_hook("pre-branch-gate", payload, synthetic)
    if res.returncode != 2:
        return False, (
            f"deny phase: expected exit 2, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
    if '"permissionDecision": "deny"' not in res.stdout:
        return False, f"deny phase: missing permissionDecision deny\nstdout: {res.stdout}"

    marker = synthetic / ".claude" / "branch-approvals" / "feat_example.approved"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()

    res = invoke_hook("pre-branch-gate", payload, synthetic)
    if res.returncode != 0:
        return False, (
            f"allow phase: expected exit 0, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )

    return True, ""


SCENARIOS = [
    ("D1", "pre-branch-gate", scenario_d1_pre_branch_gate),
]


def main() -> int:
    failures: list[str] = []
    for code, name, fn in SCENARIOS:
        tmp = Path(tempfile.mkdtemp(prefix="pos-selftest-"))
        synthetic = tmp / "synthetic"
        try:
            try:
                generate_synthetic(synthetic)
            except subprocess.CalledProcessError as e:
                print(
                    f"[fail] {code} {name}: generator failed\n"
                    f"stdout: {e.stdout}\nstderr: {e.stderr}"
                )
                failures.append(code)
                continue
            ok, reason = fn(synthetic)
            if ok:
                print(f"[ok] {code} {name}")
            else:
                print(f"[fail] {code} {name}: {reason}")
                failures.append(code)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print(f"pos-selftest: {len(failures)} scenario(s) failed: {', '.join(failures)}")
        return 1
    print(f"pos-selftest: {len(SCENARIOS)} scenario(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
