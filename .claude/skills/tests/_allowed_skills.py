"""Canonical ALLOWED_SKILLS constant for all skill contract tests.

Shared across:
  - .claude/skills/tests/test_skill_frontmatter.py (primary definition)
  - hooks/tests/test_lib_policy.py (policy validation)
  - hooks/tests/test_skills_log_contract.py (logger contract)

Contract-bound (must match policy.yaml.skills_allowed exactly), not era-bound.
Adding a skill = extend this list + policy.yaml.skills_allowed in the same branch.

Delivered:
  E1a — project-kickoff, writing-handoff
  E1b — branch-plan, deep-interview
  E2a — pre-commit-review, simplify
  E2b — compress, audit-plugin
  E3a — compound, pattern-audit
  E3b — test-scaffold, test-audit, coverage-explain
"""

ALLOWED_SKILLS = [
    "project-kickoff",
    "writing-handoff",
    "branch-plan",
    "deep-interview",
    "pre-commit-review",
    "simplify",
    "compress",
    "audit-plugin",
    "compound",
    "pattern-audit",
    "test-scaffold",
    "test-audit",
    "coverage-explain",
]
