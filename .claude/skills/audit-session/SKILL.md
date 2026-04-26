---
name: audit-session
description: Use when you want to audit a session for drift between policy.yaml declarations and the real .claude/logs/ — declares candidate signals across skills_allowed, lifecycle hooks_required, and required_logs.
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(find:*)
  - Bash(wc:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# Skill — audit-session

## Scope (strict)

**Read-only advisory.** This skill compares three surfaces of `policy.yaml` against the real state of `.claude/logs/` and DECLARES CANDIDATE DRIFT SIGNALS. It does NOT modify policy, does NOT mutate logs, does NOT auto-fix any drift it detects.

### You MAY:
- Read `policy.yaml`, files under `.claude/logs/`, and `.claude/skills/<slug>/SKILL.md` for cross-reference.
- Declare drift candidates by comparing declared state vs observed state.
- Suggest follow-up actions for the user to consider.

### You MUST NOT:
- Modify `policy.yaml` (no `Edit` / `Write` against it).
- Modify, truncate, or rotate any file under `.claude/logs/`.
- Auto-fix any drift detected (advisory contract).
- Delegate analysis to an external fork or Agent — comparison must remain main-strict (local + cheap).
- Execute `git log`, `git diff`, or any subprocess that mutates state.

## Framing

This is NOT an exhaustive auditor. This is a pattern-seeking advisor over three explicit surfaces. The signals are candidates; the user decides which are real drift and which are deliberate.

**Three surfaces audited (Fase -1 decision A1.a)**:

1. **Skills allowlist drift** — `policy.yaml.skills_allowed` (plain slugs) vs `.claude/logs/skills.jsonl` invocations. Detects: declared but never invoked (dead allowlist entry), invoked but not declared (would have been denied today by the Stop hook).
2. **Lifecycle hooks/log drift** — `policy.yaml.lifecycle.*.hooks_required` vs the per-hook log files in `.claude/logs/`. Detects: declared hook with no matching log file (hook never ran or never logged), declared hook with empty log (silently disabled), hooks logging that aren't declared in any lifecycle gate.
3. **Required logs drift** — `policy.yaml.audit.required_logs` vs file system reality. Detects: declared log file missing entirely, declared log file empty, declared log file older than the review window.

**Review window default: 30 days.** Declared in this body as textual guidance for the human reading the report — the skill does NOT execute date-math filtering of log entries, NOR does it prune old entries. The human applies the 30-day lens when reading the candidate signals (Fase -1 decision A2.a).

### Prefix normalization assumption

`policy.yaml.skills_allowed` lists plain slugs (e.g. `audit-plugin`). `policy.yaml.lifecycle.*.skills_required` lists user-facing forms (e.g. `pos:audit-plugin`). When comparing, this skill normalizes by stripping the leading `pos:` so that `pos:audit-plugin` and `audit-plugin` match. This assumption is made explicit in the report (Fase -1 decision A3.a).

## Steps

1. **Read declared state** (Read):
   - `policy.yaml` — extract: `skills_allowed`, `lifecycle.*.hooks_required` (per gate), `audit.required_logs`, `audit.retention_days`.
   - Note: do NOT enforce `audit.session_audit.schedule` (e.g. `weekly`) — that field is documental, not enforcement (Fase -1 decision A6.a).

2. **Read observed state** (Glob + Read + Bash):
   - `.claude/logs/skills.jsonl` — line count + extract distinct `skill` values (use `Grep` for `"skill":` field extraction).
   - `.claude/logs/<hook>.jsonl` for each declared hook — existence + nonempty (`Bash(wc:*)` for line count).
   - `.claude/logs/<required_log>` for each `audit.required_logs` entry — same checks; `Bash(find:*)` for mtime.

3. **Compare and classify** (3 buckets):

   **Bucket 1 — Skills allowlist drift**:
   - For each entry in `skills_allowed`: was it observed in `skills.jsonl` (any session)? If not → candidate `declared but never invoked`.
   - For each distinct skill in `skills.jsonl`: is it (after `pos:` normalization) in `skills_allowed`? If not → candidate `invoked but not declared` (would be denied today by the Stop hook for that session).

   **Bucket 2 — Lifecycle hooks/log drift**:
   - For each `lifecycle.<gate>.hooks_required` entry: does `.claude/logs/<hook-base>.jsonl` exist? Is it nonempty? Is its mtime within the 30-day review window?
   - For each `<hook>.jsonl` present in `.claude/logs/`: is its base name in any `lifecycle.*.hooks_required`? If not → candidate `logging hook not declared in any lifecycle gate`.

   **Bucket 3 — Required logs drift**:
   - For each `audit.required_logs` entry: does the file exist in `.claude/logs/`? Is it nonempty? Is its mtime within the 30-day review window? (Mtime check is advisory only; report it, do not block on it.)

4. **Report** (structured by surface, Fase -1 decision A5.a):
   - Section 1: **Skills allowlist drift** — bullets `<entry> — <type>: <reasoning>`.
   - Section 2: **Lifecycle hooks/log drift** — bullets `<entry> — <type>: <reasoning>`.
   - Section 3: **Required logs drift** — bullets `<entry> — <type>: <reasoning>`.
   - Summary line: `Found X skills drift, Y hooks/log drift, Z required logs drift. Advisory-only — user decides which are real drift, which are deliberate. Review window: 30 days. Prefix normalization: pos:<slug> ↔ <slug>.`

5. **Pre-existing drift expected (Fase -1 decision A4.a)**: at delivery time, `audit.required_logs` declares `hooks.jsonl` but no such file exists in `.claude/logs/` (hooks log to per-hook files: `pre-branch-gate.jsonl`, `pre-pr-gate.jsonl`, etc.). This skill reports the missing file as a Bucket 3 candidate — the user decides whether to update `policy.yaml` or accept the declaration as documental aspiration. **The skill does NOT auto-fix this drift.** That this finding emerges on the very first run is evidence the advisor is doing its job.

6. **STOP** — emit the report and wait. Do NOT:
   - modify `policy.yaml` to fix any drift.
   - touch, truncate, or rotate any log file.
   - propose patches; describe the candidate signals only.

7. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh audit-session ok
   ```

## Failure modes

- `policy.yaml` missing or unparseable → emit `policy unavailable` report with no comparisons; log `status: degraded`.
- `.claude/logs/` directory missing → report all declared logs as Bucket 3 drift; log `status: partial`.
- Single log file unreadable (permissions / corruption) → skip that file with a note in the report; continue with the rest; log `status: partial`.

## Explicitly out of scope

- Modifying `policy.yaml` to fix declared drift — that requires a dedicated branch with explicit user approval.
- Pruning, truncating, or rotating any log file under `.claude/logs/`.
- Enforcing `audit.session_audit.schedule` (e.g. `weekly`) — cadence is documental in F1; cron / CI hook enforcement is deferred to a later branch if signal emerges (Fase -1 decision A6.a).
- Cross-session aggregation, trend metrics, or longitudinal analysis over multiple time windows.
- Auditing `model_routing`, `testing.*`, `ci_cd.*`, `safety.*` surfaces — out-of-scope MVP; reopen via dedicated branch if signal emerges.
- Computing per-entry timestamps with date arithmetic — the 30-day review window is textual guidance for the human; the skill does not filter log entries by date.
- Delegating analysis to an external fork — main-strict by design (see CLAUDE.md regla #7 and `.claude/rules/skills.md § Fork / delegación`).
