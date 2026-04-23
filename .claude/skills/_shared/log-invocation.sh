#!/usr/bin/env bash
# Shared helper: append one line to .claude/logs/skills.jsonl describing a
# skill invocation. Called as the final step of every pos skill.
#
# Best-effort operational — not a cryptographic guarantee. If the model skips
# this step in a rare invocation, the audit log simply loses that one trace.
# The system NEVER breaks on a missing log entry (stop-policy-check treats
# absence of a log entry as "no invocation", not a violation).
#
# Shape (fixed in E1a Fase -1, cross-validated by
# hooks/tests/test_skills_log_contract.py):
#     {"ts": "<ISO-8601 UTC>", "skill": "<name>",
#      "session_id": "<CLAUDE_SESSION_ID or 'unknown'>", "status": "ok|…"}
#
# No extra fields (no args, no duration_ms) until a real need appears.
#
# Usage:
#     .claude/skills/_shared/log-invocation.sh <skill-name> [status]
#
# Environment:
#     CLAUDE_SESSION_ID   filled by Claude Code at skill invocation time;
#                         falls back to "unknown" if absent.
set -euo pipefail

skill="${1:?skill name required}"
status="${2:-ok}"
session_id="${CLAUDE_SESSION_ID:-unknown}"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
log_dir=".claude/logs"

mkdir -p "$log_dir"
printf '{"ts":"%s","skill":"%s","session_id":"%s","status":"%s"}\n' \
    "$ts" "$skill" "$session_id" "$status" \
    >> "$log_dir/skills.jsonl"
