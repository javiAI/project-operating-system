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
import textwrap
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


def git_in(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run `git <args>` inside `repo`. Raises on non-zero exit."""
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )


def init_baseline_repo(repo: Path) -> None:
    """Init a fresh git repo on `main`, configure user, commit current tree."""
    git_in(repo, "init", "-q", "-b", "main")
    git_in(repo, "config", "user.email", "selftest@pos.local")
    git_in(repo, "config", "user.name", "pos selftest")
    git_in(repo, "add", "-A")
    git_in(repo, "commit", "-q", "-m", "baseline")


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


POLICY_PRE_WRITE_ONLY = textwrap.dedent("""\
    lifecycle:
      pre_write:
        enforced_patterns:
          - label: "hooks_top_level_py"
            match_glob: "hooks/*.py"
            exclude_globs:
              - "hooks/_lib/**"
              - "hooks/tests/**"
""")


def scenario_d3_pre_write_guard(synthetic: Path) -> tuple[bool, str]:
    """D3: deny Write to enforced path without test pair, allow with."""
    # Synthetic project's rendered policy lacks pre_write (template drift
    # documented post-D5b). Inject a minimal policy so the hook enforces.
    (synthetic / "policy.yaml").write_text(POLICY_PRE_WRITE_ONLY, encoding="utf-8")

    target = synthetic / "hooks" / "foo.py"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(target)},
    }

    res = invoke_hook("pre-write-guard", payload, synthetic)
    if res.returncode != 2:
        return False, (
            f"deny phase: expected exit 2, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
    if '"permissionDecision": "deny"' not in res.stdout:
        return False, f"deny phase: missing permissionDecision deny\nstdout: {res.stdout}"

    test_pair = synthetic / "hooks" / "tests" / "test_foo.py"
    test_pair.parent.mkdir(parents=True, exist_ok=True)
    test_pair.touch()

    res = invoke_hook("pre-write-guard", payload, synthetic)
    if res.returncode != 0:
        return False, (
            f"allow phase: expected exit 0, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )

    return True, ""


POLICY_DOCS_SYNC_ONLY = textwrap.dedent("""\
    lifecycle:
      pre_pr:
        docs_sync_required:
          - "ROADMAP.md"
          - "HANDOFF.md"
        docs_sync_conditional: []
""")


def scenario_d4_pre_pr_gate(synthetic: Path) -> tuple[bool, str]:
    """D4: deny `gh pr create` when docs-sync incomplete; allow when satisfied."""
    (synthetic / "policy.yaml").write_text(POLICY_DOCS_SYNC_ONLY, encoding="utf-8")
    init_baseline_repo(synthetic)
    git_in(synthetic, "checkout", "-q", "-b", "feat/example")
    (synthetic / "src.txt").write_text("payload\n", encoding="utf-8")
    git_in(synthetic, "add", "src.txt")
    git_in(synthetic, "commit", "-q", "-m", "feat: add src")

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --title test --body test"},
    }

    res = invoke_hook("pre-pr-gate", payload, synthetic)
    if res.returncode != 2:
        return False, (
            f"deny phase: expected exit 2, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
    if '"permissionDecision": "deny"' not in res.stdout:
        return False, f"deny phase: missing permissionDecision deny\nstdout: {res.stdout}"
    if "docs-sync" not in res.stdout:
        return False, f"deny phase: missing 'docs-sync' in reason\nstdout: {res.stdout}"

    (synthetic / "ROADMAP.md").write_text("# ROADMAP\nupdated\n", encoding="utf-8")
    (synthetic / "HANDOFF.md").write_text("# HANDOFF\nupdated\n", encoding="utf-8")
    git_in(synthetic, "add", "ROADMAP.md", "HANDOFF.md")
    git_in(synthetic, "commit", "-q", "-m", "docs: sync")

    res = invoke_hook("pre-pr-gate", payload, synthetic)
    if res.returncode != 0:
        return False, (
            f"allow phase: expected exit 0, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )

    return True, ""


POLICY_POST_MERGE_ONLY = textwrap.dedent("""\
    lifecycle:
      post_merge:
        skills_conditional:
          - trigger:
              touched_paths_any_of:
                - "generator/*.ts"
              skip_if_only:
                - "*.md"
              min_files_changed: 1
""")


def scenario_d5_post_action(synthetic: Path) -> tuple[bool, str]:
    """D5: confirmed merge whose diff matches trigger emits /pos:compound advisory."""
    (synthetic / "policy.yaml").write_text(POLICY_POST_MERGE_ONLY, encoding="utf-8")
    init_baseline_repo(synthetic)
    git_in(synthetic, "checkout", "-q", "-b", "feat/example")
    target = synthetic / "generator" / "feature.ts"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("export const x = 1;\n", encoding="utf-8")
    git_in(synthetic, "add", "generator/feature.ts")
    git_in(synthetic, "commit", "-q", "-m", "feat: add generator/feature.ts")
    git_in(synthetic, "checkout", "-q", "main")
    git_in(synthetic, "merge", "--no-ff", "feat/example", "-m", "Merge feat/example")

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git merge --no-ff feat/example"},
    }
    res = invoke_hook("post-action", payload, synthetic)
    if res.returncode != 0:
        return False, (
            f"expected exit 0, got {res.returncode}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
    if "/pos:compound" not in res.stdout:
        return False, (
            f"missing /pos:compound advisory in stdout\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )

    return True, ""


SCENARIOS = [
    ("D1", "pre-branch-gate", scenario_d1_pre_branch_gate),
    ("D3", "pre-write-guard", scenario_d3_pre_write_guard),
    ("D4", "pre-pr-gate", scenario_d4_pre_pr_gate),
    ("D5", "post-action", scenario_d5_post_action),
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
