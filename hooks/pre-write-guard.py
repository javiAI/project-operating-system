#!/usr/bin/env python3
"""pre-write-guard: enforce test-pair existence on Writes to enforced paths.

PreToolUse(Write) blocker. Enforces CLAUDE.md regla #3:

- hooks/<name>.py (top-level, not in _lib/ or tests/) must have
  hooks/tests/test_<name_underscore>.py before the impl is first written.
- generator/**/*.ts (excluding *.test.ts, __tests__, __fixtures__) must have
  co-located <path>.test.ts before the impl is first written.

Edits on files that already exist → always allow (edit flow). D4's
pre-pr-gate is where missing coverage on existing files is caught.

Pass-through silent (exit 0, zero log) on: non-Write tool, excluded paths
(bucket 1: tests/docs/templates/meta; bucket 2: hooks/_lib/**), out-of-scope
paths, paths outside the repo root. Double-log to
`.claude/logs/pre-write-guard.jsonl` + `.claude/logs/phase-gates.jsonl`
(event `pre_write`) only on decisions over enforced paths. Blocker
safe-fail canonical (D1 shape, not D2 informative): malformed stdin /
JSON / top-level / tool_input → deny exit 2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "PreToolUse"
HOOK_NAME = "pre-write-guard"
HOOK_LOG = ".claude/logs/pre-write-guard.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"


def is_enforced(rel_path: str) -> bool:
    if not rel_path:
        return False
    parts = rel_path.split("/")
    if rel_path.endswith(".py"):
        return parts[0] == "hooks" and len(parts) == 2
    if rel_path.endswith(".ts"):
        if rel_path.endswith(".test.ts"):
            return False
        if parts[0] != "generator":
            return False
        if len(parts) >= 2 and parts[1] in ("__tests__", "__fixtures__"):
            return False
        return True
    return False


def expected_test_pair(rel_path: str) -> str:
    if rel_path.endswith(".py") and rel_path.startswith("hooks/"):
        name = rel_path.split("/", 1)[1]
        stem = name[:-3]
        return f"hooks/tests/test_{stem.replace('-', '_')}.py"
    if rel_path.endswith(".ts"):
        return rel_path[:-3] + ".test.ts"
    return ""


def build_deny_reason(write_path: str, expected_test: str) -> str:
    return (
        "Write blocked: test-pair required before implementation (CLAUDE.md regla #3).\n"
        f"Expected test file: {expected_test}\n"
        f"To unblock: touch {expected_test} and author a failing test first (RED), "
        "then retry the implementation Write.\n"
        "Rationale: see .claude/rules/tests.md — TDD hard-enforced on generator/** and hooks/**.\n"
        f"Blocked write: {write_path}"
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
        emit_deny("pre-write-guard: malformed stdin (not JSON).")
        return 2

    if not isinstance(payload, dict):
        emit_deny("pre-write-guard: stdin payload must be a JSON object.")
        return 2

    if payload.get("tool_name") != "Write":
        return 0

    tool_input = payload.get("tool_input")
    if tool_input is None:
        return 0
    if not isinstance(tool_input, dict):
        emit_deny("pre-write-guard: tool_input must be a JSON object.")
        return 2

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        return 0

    repo_root = Path.cwd()
    p = Path(file_path)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return 0
    else:
        rel = p.as_posix()

    if not is_enforced(rel):
        return 0

    impl_abs = repo_root / rel
    ts = now_iso()

    def log(decision: str, reason: str) -> None:
        append_jsonl(
            repo_root / HOOK_LOG,
            {"ts": ts, "hook": HOOK_NAME, "file_path": rel,
             "decision": decision, "reason": reason},
        )
        append_jsonl(
            repo_root / PHASE_LOG,
            {"ts": ts, "event": "pre_write", "file_path": rel, "decision": decision},
        )

    if impl_abs.exists():
        log("allow", "impl file already exists (edit flow)")
        return 0

    expected = expected_test_pair(rel)
    if (repo_root / expected).exists():
        log("allow", "test pair present")
        return 0

    reason = build_deny_reason(rel, expected)
    log("deny", reason)
    emit_deny(reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
