#!/usr/bin/env python3
"""session-start: emit pos snapshot as additionalContext on SessionStart.

Informational hook (SessionStart). Never denies — exit 0 always. On payload
or git error, degrades gracefully: logs an error entry and emits a minimal
additionalContext. See docs/ARCHITECTURE.md §7 Capa 1 and
.claude/rules/hooks.md for the safe-fail exception for informative hooks.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.jsonl import append_jsonl, read_jsonl  # noqa: E402
from _lib.slug import sanitize_slug  # noqa: E402
from _lib.time import now_iso  # noqa: E402

HOOK_EVENT = "SessionStart"
HOOK_NAME = "session-start"
APPROVALS_DIR = ".claude/branch-approvals"
HOOK_LOG = ".claude/logs/session-start.jsonl"
PHASE_LOG = ".claude/logs/phase-gates.jsonl"

GIT_TIMEOUT_S = 2

_PHASE_RE = re.compile(
    r"^(?:feat|fix|chore|refactor)[/_]([a-z])(\d+)-",
    re.IGNORECASE,
)


def phase_from_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    m = _PHASE_RE.match(slug)
    if not m:
        return None
    return (m.group(1) + m.group(2)).upper()


def _git(cwd: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def current_branch(cwd: Path) -> str | None:
    return _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")


def last_merge(cwd: Path) -> str | None:
    return _git(cwd, "log", "--merges", "-1", "--format=%h %s")


def _base_ref(cwd: Path) -> str | None:
    for ref in ("main", "master"):
        if _git(cwd, "rev-parse", "--verify", "--quiet", ref):
            return ref
    return None


def _diff_touches_docs(cwd: Path) -> bool:
    base = _base_ref(cwd)
    if base is None:
        return True
    out = _git(cwd, "diff", "--name-only", f"{base}..HEAD")
    if out is None:
        return True
    files = set(out.splitlines())
    return "ROADMAP.md" in files or "HANDOFF.md" in files


def derive_phase(branch: str | None, phase_log_path: Path) -> str:
    p = phase_from_slug(branch)
    if p:
        return p
    if branch in ("main", "master"):
        for entry in reversed(read_jsonl(phase_log_path)):
            p = phase_from_slug(entry.get("slug"))
            if p:
                return p
    return "unknown"


def detect_warnings(repo_root: Path, branch: str | None) -> list[str]:
    if not branch or branch in ("main", "master"):
        return []
    warnings: list[str] = []
    marker = repo_root / APPROVALS_DIR / f"{sanitize_slug(branch)}.approved"
    if not marker.exists():
        warnings.append(f"marker ausente: {marker.relative_to(repo_root)}")
    if not _diff_touches_docs(repo_root):
        warnings.append(
            "docs-sync pendiente: rama sin cambios en ROADMAP.md ni HANDOFF.md vs main"
        )
    return warnings


def build_snapshot(
    branch: str | None,
    phase: str,
    last_merge_str: str | None,
    warnings: list[str],
) -> str:
    lines = [
        "pos snapshot",
        f"Branch: {branch or '(unknown)'}",
        f"Phase: {phase}",
        f"Last merge: {last_merge_str or '(none)'}",
    ]
    if not warnings:
        lines.append("Warnings: (none)")
    else:
        lines.append("Warnings:")
        for w in warnings:
            lines.append(f"- {w}")
    return "\n".join(lines)


def emit(context: str) -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": context,
        }
    }
    print(json.dumps(out, ensure_ascii=False))


def _log_snapshot(
    repo_root: Path,
    ts: str,
    source: str | None,
    branch: str | None,
    phase: str,
    warnings: list[str],
) -> None:
    append_jsonl(
        repo_root / HOOK_LOG,
        {
            "ts": ts,
            "hook": HOOK_NAME,
            "source": source,
            "branch": branch,
            "phase": phase,
            "warnings": warnings,
        },
    )
    append_jsonl(
        repo_root / PHASE_LOG,
        {
            "ts": ts,
            "event": "session_start",
            "source": source,
            "branch": branch,
            "phase": phase,
        },
    )


def _log_error(repo_root: Path, ts: str, source: str | None, error: str) -> None:
    append_jsonl(
        repo_root / HOOK_LOG,
        {"ts": ts, "hook": HOOK_NAME, "source": source, "error": error},
    )


def main() -> int:
    raw = sys.stdin.read()
    cwd = Path.cwd()
    ts = now_iso()

    source: str | None = None
    error: str | None = None
    try:
        if not raw.strip():
            error = "empty stdin"
        else:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                error = "top-level payload not a JSON object"
            else:
                source = payload.get("source")
    except json.JSONDecodeError as exc:
        error = f"invalid JSON: {exc.msg}"

    if error is not None:
        _log_error(cwd, ts, source, error)
        emit(f"pos snapshot\n(error reading payload: {error})")
        return 0

    branch = current_branch(cwd)
    phase = derive_phase(branch, cwd / PHASE_LOG)
    lm = last_merge(cwd)
    warnings = detect_warnings(cwd, branch)
    snapshot = build_snapshot(branch, phase, lm, warnings)
    emit(snapshot)
    _log_snapshot(cwd, ts, source, branch, phase, warnings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
