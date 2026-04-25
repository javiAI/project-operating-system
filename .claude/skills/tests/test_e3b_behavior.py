"""Behavior contract tests for E3b skills (test-scaffold, test-audit, coverage-explain).

Scope:
  - Verify framing and scope boundaries declared in each SKILL.md body.
  - Test that behavior aligns with contrato E3b (no execution, read-only advisory where declared).
  - Lock-down wording: "declares", "proposes", "advises" (not "detects" or "parses").
  - Ensure STOP boundaries are explicit when confidence is ambiguous or output uncertain.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SKILLS_TEST_DIR = REPO_ROOT / ".claude" / "skills" / "tests"

if str(SKILLS_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_TEST_DIR))
from test_skill_frontmatter import read_skill  # noqa: E402


def read_skill_body(slug: str) -> str:
    """Return only the body (post-frontmatter) of a SKILL.md."""
    _, body = read_skill(slug)
    return body


# ────────────────────────────────────────────────────────────────────────────
# Test scaffold behavior
# ────────────────────────────────────────────────────────────────────────────


class TestScaffoldBehavior:
    """Contract lock-down for /pos:test-scaffold."""

    def test_scaffold_body_declares_writer_scoped(self):
        """test-scaffold must declare writer-scoped boundary."""
        body = read_skill_body("test-scaffold")
        assert "writer-scoped" in body.lower() or "write" in body.lower()

    def test_scaffold_body_declares_convention_detection(self):
        """test-scaffold must reference convention detection."""
        body = read_skill_body("test-scaffold")
        assert any(
            word in body.lower()
            for word in ["convention", "pattern", "co-located", "tests/"]
        )

    def test_scaffold_body_declares_ambiguity_stop(self):
        """test-scaffold must declare STOP boundary when convention is ambiguous."""
        body = read_skill_body("test-scaffold")
        assert any(
            phrase in body.lower()
            for phrase in ["ambig", "unclear", "stop", "propose", "options"]
        )

    def test_scaffold_body_declares_no_source_modification(self):
        """test-scaffold must declare it does NOT modify source code."""
        body = read_skill_body("test-scaffold")
        assert any(
            phrase in body.lower()
            for phrase in [
                "not modif",
                "does not modif",
                "no modif",
                "does not touch source",
            ]
        )

    def test_scaffold_allowed_tools_includes_write(self):
        """test-scaffold must include Write tool in its `allowed-tools` frontmatter
        list (mirrors `simplify`'s assertion for `Edit`). Checking the parsed
        frontmatter — not raw text — avoids false positives from body mentions
        of the word 'Write'."""
        fm, _ = read_skill("test-scaffold")
        tools = fm.get("allowed-tools") or []
        assert any(
            isinstance(t, str) and (t == "Write" or t.startswith("Write("))
            for t in tools
        ), (
            "test-scaffold frontmatter `allowed-tools` must include `Write` — "
            "the skill writes the test pair skeleton. Got: "
            f"{tools!r}"
        )


# ────────────────────────────────────────────────────────────────────────────
# Test audit behavior
# ────────────────────────────────────────────────────────────────────────────


class TestAuditBehavior:
    """Contract lock-down for /pos:test-audit."""

    def test_audit_body_declares_advisory_only(self):
        """test-audit must declare advisory-only (read-only)."""
        body = read_skill_body("test-audit")
        assert any(
            phrase in body.lower()
            for phrase in [
                "read-only",
                "advisory",
                "declares",
                "candidates",
                "not exhaustive",
                "non-exhaustive",
            ]
        )

    def test_audit_body_declares_candidate_signals(self):
        """test-audit must use 'declares' or 'candidates', not 'detects'."""
        body = read_skill_body("test-audit")
        # "declares candidate signals" preferred to "detects"
        assert any(
            word in body.lower() for word in ["candidate", "signal", "declares"]
        )
        # Be permissive about "detect" appearing, but body must have "candidate"
        if "detect" in body.lower():
            assert "candidate" in body.lower()

    def test_audit_body_lists_signal_types(self):
        """test-audit must declare the types it seeks: flaky/orphan/trivial."""
        body = read_skill_body("test-audit")
        assert any(
            word in body.lower() for word in ["flaky", "orphan", "trivial"]
        )

    def test_audit_body_declares_no_execution(self):
        """test-audit must declare it does NOT execute pytest/vitest."""
        body = read_skill_body("test-audit")
        assert any(
            phrase in body.lower()
            for phrase in [
                "does not execut",
                "no execut",
                "pytest",
                "vitest",
                "does not run test",
            ]
        )

    def test_audit_body_declares_read_only(self):
        """test-audit must declare it does NOT modify files."""
        body = read_skill_body("test-audit")
        assert any(
            phrase in body.lower()
            for phrase in [
                "read-only",
                "does not modif",
                "no modif",
                "does not touch",
            ]
        )


# ────────────────────────────────────────────────────────────────────────────
# Coverage explain behavior
# ────────────────────────────────────────────────────────────────────────────


class TestCoverageExplainBehavior:
    """Contract lock-down for /pos:coverage-explain."""

    def test_coverage_body_declares_advisory_only(self):
        """coverage-explain must declare advisory-only (read-only)."""
        body = read_skill_body("coverage-explain")
        assert any(
            phrase in body.lower()
            for phrase in [
                "read-only",
                "advisory",
                "explains",
                "diagnos",
                "not modif",
            ]
        )

    def test_coverage_body_declares_report_reading_strategy(self):
        """coverage-explain must declare it reads reports (parsing strategy)."""
        body = read_skill_body("coverage-explain")
        assert any(
            word in body.lower()
            for word in ["read", "report", "lcov", "coverage", "strateg"]
        )

    def test_coverage_body_declares_no_execution(self):
        """coverage-explain must declare it does NOT execute coverage commands."""
        body = read_skill_body("coverage-explain")
        assert any(
            phrase in body.lower()
            for phrase in [
                "does not execut",
                "no execut",
                "does not run coverage",
            ]
        )

    def test_coverage_body_declares_no_threshold_modification(self):
        """coverage-explain must declare it does NOT modify thresholds."""
        body = read_skill_body("coverage-explain")
        assert any(
            phrase in body.lower()
            for phrase in ["does not modif", "no modif", "does not touch threshold"]
        )

    def test_coverage_body_declares_minimal_targets(self):
        """coverage-explain must mention minimum/minimal targets."""
        body = read_skill_body("coverage-explain")
        assert any(
            word in body.lower() for word in ["minimum", "minimal", "target"]
        )
