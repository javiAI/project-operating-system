---
name: test-audit
description: "Use when you want to audit test suites for potential issues (declares candidate signals: flaky, orphan, trivial assertions)."
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(find:*)
  - Bash(git grep:*)
  - Bash(wc:*)
  - Bash(.claude/skills/_shared/log-invocation.sh:*)
---

# Skill — test-audit

## Scope (strict)

**Read-only advisory.** This skill analyzes test files and DECLARES CANDIDATE SIGNALS of issues. It does NOT execute tests, modify any files, or guarantee exhaustive coverage.

### You MAY:
- Read test files and analyze them statically.
- Declare candidate signals via pattern-matching and source inspection.
- Suggest follow-up actions based on the signals found.

### You MUST NOT:
- Execute `pytest`, `vitest`, `jest`, or any test runner.
- Modify test code or source code.
- Modify coverage configuration.
- Provide a guarantee of exhaustiveness (this is advisory, not comprehensive).

## Framing

This is NOT a comprehensive test auditor. This is a pattern-seeking advisor. The signals are candidates; the user decides whether they are real issues.

Three types of candidate signals:

1. **Flaky risk**: assertions inside loops or conditional branches (brittle to execution order, dependent on state).
2. **Orphan tests**: test files with imports that don't exist in the source tree (dead code risk).
3. **Trivial assertions**: `assert True`, `assert False` (never fail), assertions without meaningful comparisons (e.g., `assert x` where `x` is always truthy).

## Steps

1. **Discover test files** (Glob + Bash):
   - Use `Glob("**/*.test.ts")`, `Glob("**/*.spec.ts")`, `Glob("**/test_*.py")`, `Glob("**/tests/test_*.py")`, etc.
   - Identify the test structure and language (TypeScript/JavaScript, Python, Go, Rust, etc.).
   - Count discovered files to gauge repo test coverage scope.

2. **Analyze each test file** (Read + Grep):
   - Read the file. Parse the structure (test functions/describe blocks, imports, fixtures).
   - **Flaky risk detection** (Grep): search for assertions inside loops, conditionals, or state-dependent blocks:
     - TypeScript/JS: `for\s*\([^)]*\)\s*\{[^}]*expect\(` or `if\s*\([^)]*\)\s*\{[^}]*expect\(`
     - Python: `for .* in .*:\s+assert` or `if .*:\s+assert`
   - **Orphan test detection** (Grep + Read): parse imports and check if referenced paths exist in source:
     - Collect all `import/from` statements pointing to source code.
     - Use `Glob` to verify those paths exist; report missing ones.
   - **Trivial assertion detection** (Grep): search for meaningless assertions:
     - `assert True`, `assert False`, `assert 1`, `assert 0`, `assert ""`, `assert None`
     - Standalone `assert x` without comparison (high risk; hard to fail).

3. **Declare candidate signals** (synthesis):
   - For each signal found, record: file path, line number, pattern matched, reasoning.
   - Classify by type: orphan (highest severity) ≥ flaky > trivial.
   - Keep counts per type to summarize scope.

4. **Report** (constrain output, max 10 findings):
   - Group by severity tier (orphan findings first, then flaky, then trivial).
   - For each finding, format: `<file>:<line> — <type>: <pattern snippet> (<reasoning>)`.
   - Example: `tests/unit/foo.test.ts:15 — Flaky risk: assertion inside for-loop (assert within loop is brittle to execution order)`.
   - Include summary: "Found X orphan candidates, Y flaky candidates, Z trivial assertions. This is a static analysis sample, not exhaustive."

5. **No guarantees**: Conclude with a note: "This is advisory-only. User reviews findings and decides which are real issues. Some candidates may be false positives (e.g., intentional assert-in-loop for batch testing)."

6. **Log** (Bash call):
```bash
.claude/skills/_shared/log-invocation.sh test-audit ok
```

## Explicitly out of scope

- Running test suites to detect actual flakiness (timing issues, race conditions).
- Modifying tests or code.
- Executing coverage tools.
- Auditing coverage numbers.
- Guaranteeing exhaustive problem detection.
- Determining whether a test is "orphaned" vs "integration test with no direct import".

## Failure modes

- **No test files found**: repo might not have tests yet. Report gracefully and suggest creating tests.
- **Language unsupported**: e.g., LISP, Rust-specific patterns you don't understand. Declare limitation and skip or use generic heuristics.
- **Repo too large**: if >1000 test files, limit to a subset and report that only a sample was analyzed.
