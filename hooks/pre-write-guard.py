#!/usr/bin/env python3
"""pre-write-guard: enforce test-pair existence on Writes to enforced paths.

PreToolUse(Write) blocker. Enforces CLAUDE.md regla #3 over paths declared
in `policy.yaml § lifecycle.pre_write.enforced_patterns` (D5b policy-loader).

Test-pair derivation stays in code (_lib/policy.py::derive_test_pair)
keyed by the pattern's `label` — Fase -1 (b.1) decision.

Edits on files that already exist → always allow (edit flow). Pass-through
silent on: non-Write tool, excluded paths (pattern-level exclude_globs +
paths outside any enforced pattern), paths outside the repo root. Blocker
safe-fail canonical (D1): malformed stdin / JSON / top-level / tool_input
→ deny exit 2. Failure mode (c.2): if `policy.yaml` is missing/corrupt and
the loader returns None, the hook pass-throughs with `status: policy_unavailable`
logged — never denies blindly (avoids bricking the repo on a bad YAML edit).
"""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.policy import derive_test_pair, pre_write_rules  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "PreToolUse"
HOOK_NAME = "pre-write-guard"
HOOK_LOG = ".claude/logs/pre-write-guard.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"


def classify(rel_path: str, rules) -> str | None:
    """Return the matching pattern's `label` if the path is enforced; None otherwise."""
    if not rel_path or rules is None:
        return None
    for pattern in rules.enforced_patterns:
        if not fnmatch.fnmatchcase(rel_path, pattern.match_glob):
            continue
        if any(fnmatch.fnmatchcase(rel_path, ex) for ex in pattern.exclude_globs):
            return None
        return pattern.label
    return None


def build_deny_reason(write_path: str, expected_test: str) -> str:
    return (
        "Write blocked: test-pair required before implementation (CLAUDE.md regla #3).\n"
        f"Expected test file: {expected_test}\n"
        f"To unblock: touch {expected_test} and author a failing test first (RED), "
        "then retry the implementation Write.\n"
        "Enforced patterns declared in policy.yaml § lifecycle.pre_write.enforced_patterns.\n"
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


def _safe_append(path: Path, entry: dict) -> None:
    try:
        append_jsonl(path, entry)
    except OSError:
        pass


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
    try:
        rel = (repo_root / file_path).resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return 0

    rules = pre_write_rules(repo_root)
    if rules is None:
        _safe_append(
            repo_root / HOOK_LOG,
            {"ts": now_iso(), "hook": HOOK_NAME, "file_path": rel,
             "status": "policy_unavailable",
             "reason": "policy.yaml missing or pre_write section absent — pass-through"},
        )
        return 0

    label = classify(rel, rules)
    if label is None:
        return 0

    impl_abs = repo_root / rel
    ts = now_iso()

    def log(decision: str, reason: str) -> None:
        _safe_append(
            repo_root / HOOK_LOG,
            {"ts": ts, "hook": HOOK_NAME, "file_path": rel,
             "decision": decision, "reason": reason},
        )
        _safe_append(
            repo_root / PHASE_LOG,
            {"ts": ts, "event": "pre_write", "file_path": rel, "decision": decision},
        )

    if impl_abs.exists():
        log("allow", "impl file already exists (edit flow)")
        return 0

    expected = derive_test_pair(rel, label) or ""
    if expected and (repo_root / expected).exists():
        log("allow", "test pair present")
        return 0

    reason = build_deny_reason(rel, expected)
    log("deny", reason)
    emit_deny(reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
