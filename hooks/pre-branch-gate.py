#!/usr/bin/env python3
"""pre-branch-gate: block branch creation without an approval marker.

PreToolUse(Bash) hook enforcing CLAUDE.md regla #1 ("Fase -1 antes de cada rama").
Detects `git checkout -b`, `git switch -c`, and `git worktree add -b`. Denies
(exit 2) when `.claude/branch-approvals/<sanitized-slug>.approved` is absent.
Pass-through silent otherwise. See docs/ARCHITECTURE.md §7 Capa 1.
"""
from __future__ import annotations

import json
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_EVENT = "PreToolUse"
HOOK_NAME = "pre-branch-gate"
APPROVALS_DIR = ".claude/branch-approvals"
HOOK_LOG = ".claude/logs/pre-branch-gate.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"

GIT_GLOBAL_OPTS_WITH_ARG = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--exec-path",
    "--upload-pack",
}


def sanitize_slug(slug: str) -> str:
    return slug.replace("/", "_")


def _flag_value(args: list[str], flag: str) -> str | None:
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def extract_branch_slug(command: str) -> str | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens or tokens[0] != "git":
        return None

    idx = 1
    while idx < len(tokens) and tokens[idx].startswith("-"):
        opt = tokens[idx]
        if "=" in opt:
            idx += 1
        elif opt in GIT_GLOBAL_OPTS_WITH_ARG:
            idx += 2
        else:
            idx += 1

    if idx >= len(tokens):
        return None

    subcmd = tokens[idx]
    args = tokens[idx + 1 :]

    if subcmd == "checkout":
        return _flag_value(args, "-b")
    if subcmd == "switch":
        return _flag_value(args, "-c")
    if subcmd == "worktree" and args and args[0] == "add":
        return _flag_value(args[1:], "-b")
    return None


def marker_path(repo_root: Path, sanitized_slug: str) -> Path:
    return repo_root / APPROVALS_DIR / f"{sanitized_slug}.approved"


def append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_deny_reason(marker: Path, command: str) -> str:
    return (
        "Branch creation blocked: Fase -1 gate requires an approval marker.\n"
        f"Expected marker: {marker}\n"
        f"To approve after completing Fase -1: touch {marker}\n"
        "Read MASTER_PLAN.md §2.1 and the section for your branch before creating the marker.\n"
        f"Blocked command: {command}"
    )


def emit_deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "decisionReason": reason,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        emit_deny("pre-branch-gate: malformed stdin (not JSON).")
        return 2

    if not isinstance(payload, dict):
        emit_deny("pre-branch-gate: stdin payload must be a JSON object.")
        return 2

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if tool_input is None:
        tool_input = {}
    elif not isinstance(tool_input, dict):
        emit_deny("pre-branch-gate: tool_input must be a JSON object.")
        return 2

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    slug = extract_branch_slug(command)
    if slug is None:
        return 0

    sanitized = sanitize_slug(slug)
    repo_root = Path.cwd()
    marker = marker_path(repo_root, sanitized)
    ts = now_iso()

    def log(decision: str, reason: str) -> None:
        append_jsonl(
            repo_root / HOOK_LOG,
            {"ts": ts, "hook": HOOK_NAME, "command": command, "slug": sanitized,
             "decision": decision, "reason": reason},
        )
        append_jsonl(
            repo_root / PHASE_LOG,
            {"ts": ts, "event": "branch_creation", "slug": sanitized, "decision": decision},
        )

    if marker.exists():
        log("allow", "marker present")
        return 0

    reason = build_deny_reason(marker, command)
    log("deny", reason)
    emit_deny(reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
