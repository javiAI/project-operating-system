---
name: test-scaffold
description: Use when a source file needs a corresponding test pair file created (generates skeleton test structure).
allowed-tools:
  - Glob
  - Grep
  - Read
  - Write
  - Bash(find:*)
  - Bash(git grep:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# Skill — test-scaffold

## Scope (strict)

**Writer-scoped.** This skill creates ONLY the test pair file corresponding to a source file you provide. It does NOT modify the source file, docs, policy, hooks, or any other artifact.

### You MAY:
- Read source files to understand their structure.
- Inspect existing test pairs to detect test file location conventions (co-located: `foo.test.ts` next to `foo.ts`; dedicated dir: `tests/test_foo.py`; other patterns).
- Create the test pair file that follows the repo's detected convention.

### You MUST NOT:
- Modify source code.
- Execute tests or lint.
- Modify coverage settings or thresholds.
- Modify docs, policy, hooks, or build config.
- Create test files unless the convention is clear.

## Framing

This is NOT a test generator. This is an assistant for creating test pair scaffolds. The user owns writing meaningful tests. Your role:

1. **Detect convention** (deterministic): analyze existing test files to infer the pattern. Examples:
   - If 80%+ of tests are co-located (e.g., `src/foo.ts` → `src/foo.test.ts`), follow co-located.
   - If 80%+ are in a `tests/` directory (e.g., `src/foo.ts` → `tests/unit/foo.test.ts`), follow that.
   - If the repo mixes styles or you can't confidently determine a pattern, **STOP and propose options**.

2. **Generate skeleton only**: produce a minimal test file (imports + describe/test block + one placeholder assertion). Language-aware (TS/JS uses vitest/jest shape; Python uses pytest shape; Go/Rust as applicable).

3. **Declare STOP boundary**: if convention is ambiguous, list the options you observed and ask the user which pattern to follow.

## Steps

1. **Determine source file**: user provides the source file path (e.g., `src/utils/format.ts`).

2. **Detect convention** (Glob + Read + analysis):
   - Use `Glob("**/*.test.ts")`, `Glob("**/*.spec.ts")`, `Glob("**/test_*.py")`, etc. to find existing test files.
   - Analyze placement: co-located vs dedicated `tests/` directory vs other.
   - Tally the pattern. If one pattern accounts for 80%+ of files, it's the convention.

3. **Decide or stop**: 
   - Clear convention (≥80%) → proceed to step 4.
   - Ambiguous or split (40–60% either way) → STOP. Propose the top 2–3 patterns. Wait for user input.

4. **Generate test skeleton** (Write):
   - Create the test file at the inferred path (or user-specified if STOP was escalated).
   - Language-specific template (TypeScript: vitest/jest syntax; Python: pytest syntax).
   - Include: test file header comment + language-specific imports + describe/test block + placeholder assertion.
   - No linting; no execution. Structure only.

5. **Report and STOP**:
   - Declare what you created (file path + reasoning).
   - If any files exist at that path, halt and ask before overwriting.

6. **Log** (Bash call):
```bash
.claude/skills/_shared/log-invocation.sh test-scaffold ok
```

## Explicitly out of scope

- Generating actual test logic or assertions (user writes those).
- Running tests or checking syntax validity.
- Choosing a framework for the repo (it already has one; infer it from existing tests).
- Modifying any source file.
- Detecting or fixing flaky tests (that's `/pos:test-audit`).
- Coverage thresholds or configuration.

## Failure modes

- **Source file ambiguity**: user provides `foo` without extension → ask for full path.
- **No existing test files found**: repo might be brand new. Propose the most common convention for the stack detected (e.g., `<source>.test.ts` for TS, `tests/test_<module>.py` for Python) and ask for confirmation.
- **No source file at provided path**: halt and report the path not found.
