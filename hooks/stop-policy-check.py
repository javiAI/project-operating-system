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
  - skills_allowed declared → read `.claude/logs/skills.jsonl`, compare
    invoked vs allowed. Deny exit 2 on any violation (first violator in
    decisionReason); allow exit 0 otherwise.

Skill invocation source is `.claude/logs/skills.jsonl` — the canonical
audit log declared in policy.yaml.audit.required_logs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl  # noqa: E402
from _lib.policy import load_policy, skills_allowed_list  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "Stop"
HOOK_NAME = "stop-policy-check"
HOOK_LOG = ".claude/logs/stop-policy-check.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"
SKILLS_LOG = ".claude/logs/skills.jsonl"


def _extract_invoked_skills(repo_root: Path) -> list[str]:
    """Read `.claude/logs/skills.jsonl` and return the list of skill names.

    Corrupt lines (non-JSON or non-dict entries) and entries lacking a
    string `skill` key are silently ignored — the hook's job is enforcement
    based on what was reliably recorded, not forensics on the log itself.
    """
    log = repo_root / SKILLS_LOG
    if not log.exists():
        return []
    skills: list[str] = []
    try:
        for line in log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
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

    # Failure-mode (c.2): policy.yaml missing/malformed → pass-through.
    if load_policy(cwd) is None:
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "status": "policy_unavailable",
        })
        return 0

    # Scaffold (c.3): policy.yaml OK but no skills_allowed → deferred.
    allowed = skills_allowed_list(cwd)
    if allowed is None:
        _safe_append(cwd / HOOK_LOG, {
            "ts": ts,
            "hook": HOOK_NAME,
            "status": "deferred",
        })
        return 0

    # Enforcement live.
    invoked = _extract_invoked_skills(cwd)
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
            "decision": "deny",
            "violations": violations,
            "reason": reason,
        })
        _safe_append(cwd / PHASE_LOG, {
            "ts": ts,
            "event": "stop",
            "decision": "deny",
            "violations": violations,
        })
        return 2

    _safe_append(cwd / HOOK_LOG, {
        "ts": ts,
        "hook": HOOK_NAME,
        "decision": "allow",
        "invoked_count": len(invoked),
    })
    _safe_append(cwd / PHASE_LOG, {
        "ts": ts,
        "event": "stop",
        "decision": "allow",
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
