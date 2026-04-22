#!/usr/bin/env python3
"""stop-policy-check: Stop-event skill-allowlist enforcement (scaffold today).

Shape: D1 blocker (Stop). Safe-fail canonical — deny exit 2 on malformed
payload (the hook cannot validate its input, so it must not let it pass).

Framing (Fase -1 approval, c.3 scaffold):
  - Production enforcement is DEFERRED until `policy.yaml.skills_allowed`
    is declared. Today the meta-repo has no skills_allowed key, so every
    real invocation degrades to `status: deferred` pass-through. The
    enforcement path is tested end-to-end via fixtures, but is NOT live.
  - When E1a (or later) lands the `skills_allowed` key, this hook enforces
    end-to-end without a code refactor.

Failure modes:
  - policy.yaml missing / malformed / non-dict → log `status:
    policy_unavailable`, pass-through (exit 0).
  - policy.yaml present but no skills_allowed → log `status: deferred`,
    pass-through (exit 0). Prod state today.
  - policy.yaml `skills_allowed` present but wrong-shape (not list[str]) →
    log `status: policy_misconfigured`, pass-through (exit 0). Distinct
    from deferred so a typo doesn't silently turn enforcement off.
  - Stop payload missing / non-string `session_id` → deny exit 2
    (canonical safe-fail; we can't scope enforcement to a session).
  - skills_allowed declared → stream `.claude/logs/skills.jsonl` line-by-line,
    filter entries whose `session_id` matches the Stop payload, compare
    invoked vs allowed. Deny exit 2 on any violation (first violator in
    decisionReason); allow exit 0 otherwise.

Skill invocation source is `.claude/logs/skills.jsonl` — the canonical
audit log declared in policy.yaml.audit.required_logs. Entries are scoped
by `session_id`; entries without a matching `session_id` are ignored (the
log is append-only and accumulates across sessions).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.policy import (  # noqa: E402
    SKILLS_ALLOWED_INVALID,
    load_policy,
    skills_allowed_list,
)
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "Stop"
HOOK_NAME = "stop-policy-check"
HOOK_LOG = ".claude/logs/stop-policy-check.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"
SKILLS_LOG = ".claude/logs/skills.jsonl"


def _extract_invoked_skills(repo_root: Path, session_id: str) -> list[str]:
    """Stream `.claude/logs/skills.jsonl` and return skills for `session_id`.

    Only entries whose `session_id` equals the argument are counted. Entries
    lacking a `session_id` key, or with a non-string / mismatched value, are
    ignored — the log is append-only and accumulates across sessions, so
    enforcement must scope to the active Stop payload.

    Corrupt lines (non-JSON or non-dict entries) and entries lacking a
    string `skill` key are silently ignored — the hook's job is enforcement
    based on what was reliably recorded, not forensics on the log itself.

    Streams line-by-line (does not load the whole file) to keep memory
    bounded as the audit log grows.
    """
    log = repo_root / SKILLS_LOG
    if not log.exists():
        return []
    skills: list[str] = []
    try:
        with log.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if entry.get("session_id") != session_id:
                    continue
                name = entry.get("skill")
                if isinstance(name, str):
                    skills.append(name)
    except OSError:
        return []
    return skills


def _validate(invoked: list[str], allowed: tuple[str, ...]) -> tuple[str, list[str]]:
    """Return `("deny", violations)` if any invoked skill is outside the
    allowlist, else `("allow", [])`. An empty allowlist denies every
    invocation by construction (explicit deny-all is a valid policy)."""
    allowed_set = set(allowed)
    violations = [s for s in invoked if s not in allowed_set]
    return ("deny" if violations else "allow", violations)


def _safe_append(path: Path, entry: dict) -> None:
    try:
        append_jsonl(path, entry)
    except OSError:
        pass


def _emit_deny(reason: str) -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "decisionReason": reason,
        }
    }
    print(json.dumps(out, ensure_ascii=False))


def _deny_payload(cwd: Path, ts: str, reason: str) -> int:
    _emit_deny(reason)
    _safe_append(cwd / HOOK_LOG, {
        "ts": ts,
        "hook": HOOK_NAME,
        "decision": "deny",
        "reason": reason,
    })
    return 2


def main() -> int:
    raw = sys.stdin.read()
    cwd = Path.cwd()
    ts = now_iso()

    # D1 blocker safe-fail: malformed payload → deny exit 2.
    if not raw.strip():
        return _deny_payload(cwd, ts, "malformed payload: empty stdin")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return _deny_payload(
            cwd, ts, f"malformed payload: invalid JSON ({exc.msg})"
        )
    if not isinstance(payload, dict):
        return _deny_payload(
            cwd, ts, "malformed payload: top-level not a JSON object"
        )

    # Session scoping — enforcement cannot safely run without a session_id
    # to attribute invocations to. The Stop payload is documented to include
    # it, so absence is a malformed payload (safe-fail deny, D1 canonical).
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return _deny_payload(
            cwd, ts, "malformed payload: missing or non-string session_id"
        )

    # Failure-mode (c.2): policy.yaml missing/malformed → pass-through.
    if load_policy(cwd) is None:
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "status": "policy_unavailable",
        })
        return 0

    # Scaffold (c.3): tri-state on skills_allowed.
    allowed = skills_allowed_list(cwd)
    if allowed is SKILLS_ALLOWED_INVALID:
        # Present but wrong-shape → observable misconfiguration, NOT deferred.
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "status": "policy_misconfigured",
            "reason": "skills_allowed is present in policy.yaml but not a list of strings",
        })
        return 0
    if allowed is None:
        # Section absent → deferred (prod state today).
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "status": "deferred",
        })
        return 0

    # Enforcement live — scope by session_id.
    invoked = _extract_invoked_skills(cwd, session_id)
    decision, violations = _validate(invoked, allowed)

    if decision == "deny":
        first = violations[0]
        reason = (
            f"skill '{first}' is not in policy.yaml skills_allowed. "
            "Add it to the allowlist or revert the invocation."
        )
        _emit_deny(reason)
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "session_id": session_id,
            "decision": "deny",
            "violations": violations,
            "reason": reason,
        })
        _safe_append(cwd / PHASE_LOG, {
            "ts": ts,
            "event": "stop",
            "session_id": session_id,
            "decision": "deny",
            "violations": violations,
        })
        return 2

    _safe_append(cwd / HOOK_LOG, {
        "ts": ts,
        "hook": HOOK_NAME,
        "session_id": session_id,
        "decision": "allow",
        "invoked_count": len(invoked),
    })
    _safe_append(cwd / PHASE_LOG, {
        "ts": ts,
        "event": "stop",
        "session_id": session_id,
        "decision": "allow",
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
