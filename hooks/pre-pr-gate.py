#!/usr/bin/env python3
"""pre-pr-gate: block `gh pr create` when docs-sync is incomplete.

PreToolUse(Bash) blocker for CLAUDE.md regla #2. Mirrors
policy.yaml.lifecycle.pre_pr.docs_sync_* as hardcoded rules (policy-driven
parse deferred). Advisory scaffold (skills / ci_dry_run / invariants) logged
as `deferred` on every real decision. Shape: D1 blocker.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "PreToolUse"
HOOK_NAME = "pre-pr-gate"
PHASE_EVENT = "pre_pr"
HOOK_LOG = ".claude/logs/pre-pr-gate.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"

DOCS_BASELINE = ["ROADMAP.md", "HANDOFF.md"]

# (path_prefix, required_doc, excluded_prefix_or_None)
# NOTE: `hooks/tests/` exclusion is a deliberate D4 divergence — policy.yaml
# currently lists `hooks/**` uniformly. Convergence (hook ↔ policy parity)
# deferred to the policy-loader rama; see MASTER_PLAN.md § Rama D4.
CONDITIONAL_RULES = [
    ("generator/", "docs/ARCHITECTURE.md", None),
    ("hooks/", "docs/ARCHITECTURE.md", "hooks/tests/"),
    ("skills/", ".claude/rules/skills-map.md", None),
    (".claude/patterns/", "docs/ARCHITECTURE.md", None),
]

ADVISORY_CHECKS = [
    ("skills_required", "skills not yet landed (Fase E*)"),
    ("ci_dry_run_required", "ci_dry_run deferred to dedicated rama"),
    ("invariants_check", "invariants directory empty — deferred"),
]


# --- classifiers --------------------------------------------------------


def is_gh_pr_create(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    return len(tokens) >= 3 and tokens[:3] == ["gh", "pr", "create"]


def _conditional_triggers(files: list[str]) -> dict[str, list[str]]:
    triggers: dict[str, list[str]] = {}
    for path in files:
        for prefix, required_doc, exclude in CONDITIONAL_RULES:
            if not path.startswith(prefix):
                continue
            if exclude and path.startswith(exclude):
                continue
            triggers.setdefault(required_doc, []).append(path)
            break
    return triggers


def check_docs_sync(files: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Return (missing_docs, trigger_paths_capped_at_3_per_doc)."""
    file_set = set(files)
    missing: list[str] = [d for d in DOCS_BASELINE if d not in file_set]
    triggers: dict[str, list[str]] = {}
    for doc, paths in _conditional_triggers(files).items():
        if doc in file_set:
            continue
        if doc not in missing:
            missing.append(doc)
        triggers[doc] = paths[:3]
    return missing, triggers


# --- git helpers --------------------------------------------------------


def _run_git(repo_root: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def current_branch(repo_root: Path) -> str | None:
    out = _run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    if out is None:
        return None
    return out.strip() or None


def resolve_base(repo_root: Path) -> str | None:
    out = _run_git(repo_root, "merge-base", "HEAD", "main")
    if out is None:
        return None
    return out.strip() or None


def diff_files(repo_root: Path, base: str) -> list[str] | None:
    """Return file list touched between `base` and HEAD.

    Returns `None` when git is unavailable — distinct from `[]` (truly empty
    diff) so callers can skip with an explicit reason instead of denying as
    empty PR.
    """
    out = _run_git(repo_root, "diff", "--name-only", base, "HEAD")
    if out is None:
        return None
    return [line for line in out.splitlines() if line.strip()]


# --- reason builders ----------------------------------------------------


def build_empty_diff_reason(base: str) -> str:
    return (
        "PR creation blocked: no changes between merge-base and HEAD (empty PR).\n"
        f"Base: {base}\n"
        "Commit your work on the branch before running `gh pr create`."
    )


def build_docs_deny_reason(missing: list[str], files: list[str]) -> str:
    full = _conditional_triggers(files)
    lines = [
        "PR creation blocked: docs-sync incomplete (CLAUDE.md regla #2).",
        "",
        "Missing docs in diff:",
    ]
    for doc in missing:
        if doc in DOCS_BASELINE:
            lines.append(f"  - {doc} — required baseline (every PR)")
            continue
        paths = full.get(doc, [])
        display = paths[:3]
        extra = len(paths) - len(display)
        path_str = ", ".join(display)
        if extra > 0:
            path_str += f" ... (+{extra} more)"
        lines.append(f"  - {doc} — required by {path_str}")
    lines.append("")
    lines.append("Update the missing docs on this branch and re-run `gh pr create`.")
    return "\n".join(lines)


# --- output + logging ---------------------------------------------------


def emit_deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "decisionReason": reason,
        }
    }, ensure_ascii=False))


def _log_skip(repo_root: Path, ts: str, command: str, reason: str) -> None:
    append_jsonl(
        repo_root / HOOK_LOG,
        {"ts": ts, "hook": HOOK_NAME, "command": command,
         "status": "skipped", "reason": reason},
    )


def _log_decision(repo_root: Path, ts: str, command: str,
                  decision: str, reason: str) -> None:
    append_jsonl(
        repo_root / HOOK_LOG,
        {"ts": ts, "hook": HOOK_NAME, "command": command,
         "decision": decision, "reason": reason},
    )
    append_jsonl(
        repo_root / PHASE_LOG,
        {"ts": ts, "event": PHASE_EVENT, "decision": decision},
    )
    for check, note in ADVISORY_CHECKS:
        append_jsonl(
            repo_root / HOOK_LOG,
            {"ts": ts, "hook": HOOK_NAME, "status": "deferred",
             "check": check, "note": note},
        )


# --- main ---------------------------------------------------------------


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        emit_deny("pre-pr-gate: malformed stdin (not JSON).")
        return 2
    if not isinstance(payload, dict):
        emit_deny("pre-pr-gate: stdin payload must be a JSON object.")
        return 2
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = {}
    elif not isinstance(tool_input, dict):
        emit_deny("pre-pr-gate: tool_input must be a JSON object.")
        return 2

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0
    if not is_gh_pr_create(command):
        return 0

    repo_root = Path.cwd()
    ts = now_iso()

    branch = current_branch(repo_root)
    if branch is None:
        _log_skip(repo_root, ts, command, "skipped: git unavailable")
        return 0
    if branch in ("main", "master"):
        _log_skip(repo_root, ts, command, f"skipped: on {branch} branch")
        return 0
    if branch == "HEAD":
        _log_skip(repo_root, ts, command, "skipped: detached HEAD")
        return 0

    base = resolve_base(repo_root)
    if base is None:
        _log_skip(repo_root, ts, command,
                  "skipped: merge-base HEAD main unresolved")
        return 0

    files = diff_files(repo_root, base)
    if files is None:
        _log_skip(repo_root, ts, command,
                  "skipped: git diff unavailable")
        return 0
    if not files:
        reason = build_empty_diff_reason(base)
        _log_decision(repo_root, ts, command, "deny", reason)
        emit_deny(reason)
        return 2

    missing, _ = check_docs_sync(files)
    if missing:
        reason = build_docs_deny_reason(missing, files)
        _log_decision(repo_root, ts, command, "deny", reason)
        emit_deny(reason)
        return 2

    _log_decision(repo_root, ts, command, "allow", "docs-sync satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
