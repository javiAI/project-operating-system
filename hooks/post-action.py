#!/usr/bin/env python3
"""post-action: suggest /pos:compound after relevant local merges.

D5 PostToolUse(Bash) hook — non-blocking (exit 0 always). Hierarchical
detection:

Tier 1 (command match, shlex-parsed):
    A = `git merge <ref>`  (excludes --abort|--quit|--continue|--skip)
    C = `git pull`         (excludes --rebase / -r)
Tier 2 (post-hoc reflog confirmation):
    A expects HEAD reflog message to start with "merge ".
    C expects "pull:" or "pull " (and NOT "pull --rebase").

When both tiers confirm and `git diff --name-only HEAD@{1} HEAD` yields paths
that match the hardcoded mirror of
policy.yaml.lifecycle.post_merge.skills_conditional[0].trigger, emits
additionalContext suggesting `/pos:compound`. Never dispatches the skill.

Shape emparentado con D1 blocker (shlex + double log + importlib-friendly)
but PostToolUse non-blocking — nunca emite permissionDecision ni exit 2.
"""
from __future__ import annotations

import fnmatch
import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.policy import PostMergeTrigger, post_merge_trigger  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "PostToolUse"
HOOK_NAME = "post-action"
PHASE_EVENT = "post_merge"
HOOK_LOG = ".claude/logs/post-action.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"

_MERGE_CONTROL_FLAGS = {"--abort", "--quit", "--continue", "--skip"}
_PULL_REBASE_FLAGS = {"--rebase", "-r"}

_TOUCHED_DISPLAY_CAP = 3


# --- classifiers --------------------------------------------------------


def classify_command(command: str) -> str | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if len(tokens) < 2 or tokens[0] != "git":
        return None
    if tokens[1] == "merge":
        if any(t in _MERGE_CONTROL_FLAGS for t in tokens[2:]):
            return None
        return "git_merge"
    if tokens[1] == "pull":
        if any(t in _PULL_REBASE_FLAGS for t in tokens[2:]):
            return None
        return "git_pull"
    return None


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


def reflog_message(repo_root: Path) -> str | None:
    out = _run_git(repo_root, "reflog", "HEAD", "-1", "--format=%gs")
    if out is None:
        return None
    return out.strip() or None


def reflog_confirms(kind: str, reflog: str | None) -> bool:
    if not reflog:
        return False
    if kind == "git_merge":
        return reflog.startswith("merge ")
    if kind == "git_pull":
        if reflog.startswith("pull --rebase"):
            return False
        return reflog.startswith("pull:") or reflog.startswith("pull ")
    return False


def touched_paths(repo_root: Path) -> list[str] | None:
    out = _run_git(repo_root, "diff", "--name-only", "HEAD@{1}", "HEAD")
    if out is None:
        return None
    return [line for line in out.splitlines() if line.strip()]


# --- trigger matching ---------------------------------------------------


def match_triggers(paths: list[str], trigger: PostMergeTrigger) -> list[str]:
    if len(paths) < trigger.min_files_changed:
        return []
    if all(any(fnmatch.fnmatchcase(p, g) for g in trigger.skip_if_only) for p in paths):
        return []
    return [
        glob for glob in trigger.touched_paths_any_of
        if any(fnmatch.fnmatchcase(p, glob) for p in paths)
    ]


# --- output builder -----------------------------------------------------


def build_additional_context(triggers: list[str], touched: list[str]) -> str:
    display = touched[:_TOUCHED_DISPLAY_CAP]
    extra = len(touched) - len(display)
    touched_str = ", ".join(display)
    if extra > 0:
        touched_str += f" ... (+{extra} more)"
    return (
        "D5 post_merge: compound triggers matched.\n"
        f"Matched trigger globs: {', '.join(triggers)}\n"
        f"Touched: {touched_str}\n"
        "Consider running /pos:compound to extract reusable patterns."
    )


def emit_additional_context(ctx: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": ctx,
        }
    }, ensure_ascii=False))


# --- logging ------------------------------------------------------------


def _safe_append(path: Path, entry: dict) -> None:
    try:
        append_jsonl(path, entry)
    except OSError:
        pass


def _log_hook(repo_root: Path, entry: dict) -> None:
    _safe_append(repo_root / HOOK_LOG, entry)


def _log_phase(repo_root: Path, ts: str) -> None:
    _safe_append(repo_root / PHASE_LOG, {"ts": ts, "event": PHASE_EVENT})


# --- main ---------------------------------------------------------------


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    kind = classify_command(command)
    if kind is None:
        return 0

    repo_root = Path.cwd()
    ts = now_iso()

    trigger = post_merge_trigger(repo_root)
    if trigger is None:
        _log_hook(repo_root, {
            "ts": ts, "hook": HOOK_NAME, "command": command,
            "kind": kind, "status": "policy_unavailable",
            "reason": "policy.yaml missing or post_merge trigger absent",
        })
        return 0

    reflog = reflog_message(repo_root)
    if not reflog_confirms(kind, reflog):
        _log_hook(repo_root, {
            "ts": ts, "hook": HOOK_NAME, "command": command,
            "kind": kind, "status": "tier2_unconfirmed",
            "reflog": reflog or "",
        })
        return 0

    paths = touched_paths(repo_root)
    if paths is None:
        _log_hook(repo_root, {
            "ts": ts, "hook": HOOK_NAME, "command": command,
            "kind": kind, "status": "diff_unavailable",
            "reflog": reflog,
        })
        return 0

    triggers = match_triggers(paths, trigger)
    if not triggers:
        _log_hook(repo_root, {
            "ts": ts, "hook": HOOK_NAME, "command": command,
            "kind": kind, "status": "confirmed_no_triggers",
            "touched_paths": paths,
        })
        _log_phase(repo_root, ts)
        return 0

    _log_hook(repo_root, {
        "ts": ts, "hook": HOOK_NAME, "command": command,
        "kind": kind, "status": "confirmed_triggers_matched",
        "touched_paths": paths,
        "triggers_matched": triggers,
    })
    _log_phase(repo_root, ts)
    emit_additional_context(build_additional_context(triggers, paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
