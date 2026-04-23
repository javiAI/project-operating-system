#!/usr/bin/env python3
"""pre-compact: emit persist checklist as additionalContext on PreCompact.

Informative hook (PreCompact). Never denies — exit 0 always. The `persist`
items declared in `policy.yaml.lifecycle.pre_compact` become a reminder to
the model to write volatile state to its durable home before the compact
operation truncates the conversation.

Failure-mode (c.2): missing / malformed / pre_compact-absent policy → minimal
`additionalContext` + `status: policy_unavailable` in the hook log. Never
deny blind — blocking a user-invoked `/compact` would be destructive and the
loader's pass-through advisory contract is the canonical response.

Payload errors (empty stdin, invalid JSON, non-object top level) log under
`status: payload_error` and emit a minimal error context. Logging failures
are swallowed to preserve the exit-0 contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.policy import pre_compact_rules  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "PreCompact"
HOOK_NAME = "pre-compact"
HOOK_LOG = ".claude/logs/pre-compact.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"


def build_context(persist_items: tuple[str, ...]) -> str:
    header = [
        "pos pre-compact: persist volatile state before truncation",
        "",
        "Before the compact runs, persist the following items to their",
        "durable homes so they survive conversation history truncation:",
        "",
    ]
    if not persist_items:
        return "\n".join(header + ["  (no persist items declared in policy.yaml)"])
    return "\n".join(header + [f"  - {item}" for item in persist_items])


def unavailable_context() -> str:
    return (
        "pos pre-compact: policy unavailable\n"
        "(policy.yaml missing, malformed, or lacking a pre_compact section — "
        "no persist checklist to emit)"
    )


def emit(context: str) -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": context,
        }
    }
    print(json.dumps(out, ensure_ascii=False))


def _safe_append(path: Path, entry: dict) -> None:
    try:
        append_jsonl(path, entry)
    except OSError:
        pass


def main() -> int:
    raw = sys.stdin.read()
    cwd = Path.cwd()
    ts = now_iso()

    trigger: str | None = None
    error: str | None = None
    try:
        if not raw.strip():
            error = "empty stdin"
        else:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                error = "top-level payload not a JSON object"
            else:
                trigger = payload.get("trigger")
    except json.JSONDecodeError as exc:
        error = f"invalid JSON: {exc.msg}"

    if error is not None:
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "trigger": trigger,
            "status": "payload_error",
            "error": error,
        })
        emit(f"pos pre-compact\n(error reading payload: {error})")
        return 0

    rules = pre_compact_rules(cwd)
    if rules is None:
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "trigger": trigger,
            "status": "policy_unavailable",
        })
        emit(unavailable_context())
        return 0

    emit(build_context(rules.persist))
    _safe_append(cwd / HOOK_LOG, {
        "ts": ts,
        "hook": HOOK_NAME,
        "trigger": trigger,
        "status": "ok",
        "persist_count": len(rules.persist),
    })
    _safe_append(cwd / PHASE_LOG, {
        "ts": ts,
        "event": "pre_compact",
        "trigger": trigger,
        "status": "ok",
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
