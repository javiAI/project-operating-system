---
name: simplify
description: Use when the user asks to "simplifica antes del PR", "quita redundancia", "pasada de simplify", "pasa simplify a la rama", or just before `/pos:pre-commit-review`. Reduces redundancia, ruido, accidental complexity and premature abstraction in files already present in the branch diff (`git diff --name-only main...HEAD`). Writer-scoped — edits files in the diff, does not create new files, does not touch files outside the diff. Does not find bugs. Does not change behavior. No major refactor. Reports what it simplified and what it decided not to touch.
allowed-tools:
  - Read
  - Grep
  - Edit
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(git merge-base:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# simplify

Reduce redundancia, ruido, accidental complexity and premature abstraction in the files that this branch already touched. Run before `pre-commit-review` so the review operates on the leanest version of the diff.

Framing: this is an eligibility hint, not a guaranteed auto-trigger. Claude Code decides whether to activate you based on `description`. Invocation is typically user-triggered pre-PR.

## Scope (strict, writer-scoped)

You MAY edit files that are **already present** in `git diff --name-only main..HEAD` — this is the only set of paths the skill is allowed to mutate. Derive the set deterministically at step 1; do NOT guess it.

You MUST NOT:
- Create new files. The skill does not create new files. If a reduction would require a new helper, module, or test, emit that as a note for the user (or for `pre-commit-review`). Never call `Write` on a path not already in the diff.
- Touch files outside the diff. Even if a stale comment in an unrelated file catches your eye, files outside the diff are out of scope. The skill does not touch files outside the diff.
- Find bugs. The skill does not find bugs — `pre-commit-review` is the bug finder. If you suspect a bug while simplifying, surface it as a note and move on; do NOT fix it here.
- Change behavior. The skill does not change behavior. Every edit must preserve observable behavior. If a simplification would change behavior (e.g., removing a guard that only looked "defensive"), stop and surface it as a question for the user.
- Do a major refactor. No major refactor: no file moves, no API renames that ripple across the repo, no structural redesigns, no new public surface. Reductions are local to the touched files.
- Replace `pre-commit-review`. They are complementary. `simplify` runs first; `pre-commit-review` runs on the reduced diff.

## What counts as a simplification

Target:
- **Redundancia**: duplicated strings, parallel code paths that collapse into one, unused imports, branches that reach the same outcome, redundancy in docstrings repeating the signature.
- **Ruido / noise**: stale comments, dead code, over-long variable names that add nothing, debug prints left in. Ruido y noise son targets explícitos.
- **Complejidad accidental / accidental complexity**: conditionals that are hard to follow but simplify to a boolean, state that can be dropped, intermediate variables with a single use.
- **Abstracción prematura / premature abstraction**: helpers with a single caller, indirections that hide the simple shape, generic type parameters with one concrete use.

Do NOT target:
- Bugs (that's `pre-commit-review`).
- Style-only changes that don't reduce anything.
- Refactors that grow the diff.
- Rewrites motivated by taste.

## Steps

1. **Derive the scope**. Compute the set of touched paths deterministically:

   ```bash
   git merge-base main HEAD
   git diff --name-only main...HEAD
   ```

   Store the list. Every subsequent `Edit` call MUST target a file in this list. Paths not in the list are out of scope, period. The skill does not create new files and does not touch files outside the diff.

2. **Read the full diff**:

   ```bash
   git diff main...HEAD
   ```

   Identify candidate reductions against the targets above. Skip anything that looks like a bug or a behavior change — note it separately; this skill does not find bugs and does not change behavior.

3. **Classify each candidate**, grouped by file:
   - `apply` — straightforward reduction, behavior-preserving, small diff.
   - `skip` — reason is one of: out of diff, would create a new file, would change behavior, would need a major refactor, looks like a bug, taste-only.

4. **Apply the `apply` items** with `Edit`. Scope check every call: the `file_path` must match an entry from step 1. If it doesn't, do NOT edit — re-classify as `skip (out of scope)`.

5. **Report**. Emit a two-part summary in this conversation:
   - **Qué simplificó / what was simplified**: one bullet per reduction applied, with file and a ≤1-line description.
   - **Qué decidió no tocar / what it chose not to touch**: one bullet per candidate marked `skip`, with the reason (out of diff, would need new file, behavior change, potential bug, major refactor, taste-only).

   Keep the report tight. The user should see at a glance what moved and why the rest was left alone.

6. **Log the invocation** (best-effort — last step, never blocks):

   ```bash
   .claude/skills/_shared/log-invocation.sh simplify ok
   ```

## Failure modes

- HEAD is `main` / `master`, or `git diff main..HEAD` is empty → nothing to simplify; stop. Log `status: partial`.
- `git merge-base main HEAD` fails (detached HEAD, no common base) → stop and tell the user; do not guess the scope. Log `status: partial`.
- An `Edit` call would create a new file (path not yet tracked) → abort that edit, re-classify as `skip (would create new file)`, continue with the rest. Log `status: partial` if any candidate was forcibly skipped this way.
- Reduction unexpectedly changes behavior (realized mid-edit) → revert with a second `Edit`, re-classify as `skip (behavior change)`, continue. The invariant is behavior preservation, not completing every candidate.

## Explicitly out of scope

- Creating new files (helpers, modules, tests). The skill does not create new files. If a reduction would need one, note it as a follow-up.
- Touching files outside the branch diff. The skill does not touch files outside the diff. Even cleanup-looking changes in adjacent files are out of scope — they belong in their own branch.
- Finding bugs. The skill does not find bugs — that's `pre-commit-review`.
- Changing behavior intentionally. The skill does not change behavior. Every edit must preserve observable behavior.
- Major refactors. No major refactor: no file moves, no API renames rippling across the repo, no structural redesigns.
- Replacing `pre-commit-review`. Canonical order: `simplify → pre-commit-review`.
- Opening the PR (`gh pr create`). User-gated; `pre-pr-gate` hook enforces docs-sync independently.
