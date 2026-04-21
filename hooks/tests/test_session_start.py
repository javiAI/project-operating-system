"""Tests for hooks/session-start.py."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "session-start.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

_spec = importlib.util.spec_from_file_location("session_start", HOOK)
assert _spec is not None and _spec.loader is not None
ss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ss)


GIT_ENV_BASE = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@test.example",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@test.example",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
}


def _env() -> dict:
    return {**os.environ, **GIT_ENV_BASE}


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
        env=_env(),
    )


def run_hook(payload, cwd: Path) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
        env=_env(),
    )


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def parse_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout) if result.stdout.strip() else {}


def additional_context(result: subprocess.CompletedProcess) -> str:
    out = parse_stdout(result)
    return out["hookSpecificOutput"]["additionalContext"]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Fresh tmp repo on `main` with one initial commit and the pos dirs."""
    (tmp_path / ".claude" / "branch-approvals").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("init\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "initial")
    return tmp_path


def checkout_feat(repo: Path, slug: str = "feat/d2-test") -> None:
    """Create and switch to a feat branch with a non-trivial change."""
    git(repo, "checkout", "-q", "-b", slug)


def place_marker(repo: Path, sanitized_slug: str) -> None:
    (repo / ".claude" / "branch-approvals" / f"{sanitized_slug}.approved").touch()


def seed_phase_log(repo: Path, entries: list[dict]) -> None:
    log = repo / ".claude" / "logs" / "phase-gates.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Output envelope
# ─────────────────────────────────────────────────────────────────────────────


class TestOutputEnvelope:
    def test_always_exits_zero(self, repo: Path):
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_hook_event_name_is_session_start(self, repo: Path):
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        out = parse_stdout(result)
        assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    def test_has_additional_context(self, repo: Path):
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        assert "additionalContext" in parse_stdout(result)["hookSpecificOutput"]

    def test_never_emits_permission_decision(self, repo: Path):
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        out = parse_stdout(result)
        assert "permissionDecision" not in out["hookSpecificOutput"]


# ─────────────────────────────────────────────────────────────────────────────
# Snapshot shape (<=10 lines, ordered: branch / phase / last merge / warnings)
# ─────────────────────────────────────────────────────────────────────────────


class TestSnapshotShape:
    def test_at_most_10_lines(self, repo: Path):
        checkout_feat(repo, "feat/d2-hook-session-start")
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        ctx = additional_context(result)
        lines = [l for l in ctx.splitlines() if l.strip()]
        assert len(lines) <= 10, ctx

    def test_mentions_branch(self, repo: Path):
        checkout_feat(repo, "feat/d2-hook-session-start")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "feat/d2-hook-session-start" in ctx

    def test_contains_phase_label(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "Phase" in ctx

    def test_contains_last_merge_label(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "Last merge" in ctx

    def test_contains_warnings_label(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "Warnings" in ctx

    def test_none_literal_when_no_warnings(self, repo: Path):
        # main branch + no phase-gates log = snapshot without warnings
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "(none)" in ctx

    def test_branch_line_precedes_phase_line(self, repo: Path):
        checkout_feat(repo, "feat/d2-test")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        branch_idx = ctx.index("Branch")
        phase_idx = ctx.index("Phase")
        assert branch_idx < phase_idx

    def test_phase_line_precedes_last_merge_line(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert ctx.index("Phase") < ctx.index("Last merge")

    def test_last_merge_line_precedes_warnings_line(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert ctx.index("Last merge") < ctx.index("Warnings")


# ─────────────────────────────────────────────────────────────────────────────
# Phase derivation (C1: name → phase; fallback on main/master; else unknown)
# ─────────────────────────────────────────────────────────────────────────────


class TestPhaseDerivationFromBranch:
    def test_feat_letter_num(self, repo: Path):
        checkout_feat(repo, "feat/d2-hook-session-start")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "D2" in ctx

    def test_fix_letter_num(self, repo: Path):
        checkout_feat(repo, "fix/c5-tildes")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "C5" in ctx

    def test_chore_letter_num(self, repo: Path):
        checkout_feat(repo, "chore/b1-scaffold")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "B1" in ctx

    def test_non_matching_branch_is_unknown(self, repo: Path):
        checkout_feat(repo, "feat/no-pattern-here")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "unknown" in ctx.lower()


class TestPhaseDerivationFallbackOnMain:
    def test_main_falls_back_to_phase_log_event(self, repo: Path):
        seed_phase_log(repo, [
            {"ts": "2026-01-01T00:00:00Z", "event": "branch_creation", "slug": "feat_d1-hook-pre-branch-gate", "decision": "allow"},
        ])
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "D1" in ctx

    def test_main_without_log_is_unknown(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "unknown" in ctx.lower()

    def test_main_with_empty_log_is_unknown(self, repo: Path):
        (repo / ".claude" / "logs" / "phase-gates.jsonl").write_text("")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "unknown" in ctx.lower()

    def test_main_uses_last_log_entry_not_first(self, repo: Path):
        seed_phase_log(repo, [
            {"ts": "2026-01-01T00:00:00Z", "event": "branch_creation", "slug": "feat_c5-old", "decision": "allow"},
            {"ts": "2026-02-01T00:00:00Z", "event": "branch_creation", "slug": "feat_d1-newer", "decision": "allow"},
        ])
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "D1" in ctx
        assert "C5" not in ctx

    def test_malformed_log_line_does_not_crash(self, repo: Path):
        log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        log.write_text('not valid json\n{"ts":"2026-01-01","event":"branch_creation","slug":"feat_d1-x"}\n')
        result = run_hook(load_fixture("session_startup.json"), cwd=repo)
        assert result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Warnings (F: marker missing, E1: docs-sync)
# ─────────────────────────────────────────────────────────────────────────────


class TestMarkerWarning:
    def test_feat_branch_without_marker_emits_warning(self, repo: Path):
        checkout_feat(repo, "feat/d2-hook-session-start")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "marker" in ctx.lower()
        assert "feat_d2-hook-session-start.approved" in ctx

    def test_feat_branch_with_marker_no_warning(self, repo: Path):
        checkout_feat(repo, "feat/d2-hook-session-start")
        place_marker(repo, "feat_d2-hook-session-start")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "marker ausente" not in ctx.lower()
        assert "marker missing" not in ctx.lower()

    def test_main_branch_no_marker_warning(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "marker" not in ctx.lower()

    def test_slug_sanitized_in_marker_check(self, repo: Path):
        checkout_feat(repo, "feat/d2/nested/slashes")
        place_marker(repo, "feat_d2_nested_slashes")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "marker" not in ctx.lower()


class TestDocsSyncWarning:
    def test_feat_without_roadmap_handoff_diff_warns(self, repo: Path):
        checkout_feat(repo, "feat/d2-test")
        # touch only an unrelated file
        (repo / "some_code.py").write_text("pass\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "code only")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "docs-sync" in ctx.lower() or "docs sync" in ctx.lower()

    def test_feat_with_roadmap_diff_no_warning(self, repo: Path):
        (repo / "ROADMAP.md").write_text("# roadmap\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "add roadmap to main")
        checkout_feat(repo, "feat/d2-test")
        (repo / "ROADMAP.md").write_text("# roadmap\n\n- updated\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "update roadmap")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "docs-sync" not in ctx.lower()
        assert "docs sync" not in ctx.lower()

    def test_feat_with_handoff_diff_no_warning(self, repo: Path):
        (repo / "HANDOFF.md").write_text("# handoff\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "add handoff to main")
        checkout_feat(repo, "feat/d2-test")
        (repo / "HANDOFF.md").write_text("# handoff\n\n- updated\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "update handoff")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "docs-sync" not in ctx.lower()
        assert "docs sync" not in ctx.lower()

    def test_main_branch_no_docs_sync_warning(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "docs-sync" not in ctx.lower()
        assert "docs sync" not in ctx.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Source invariance (H1: same output across startup/resume/clear/compact)
# ─────────────────────────────────────────────────────────────────────────────


class TestSourceInvariance:
    def _ctx(self, repo, fixture):
        return additional_context(run_hook(load_fixture(fixture), cwd=repo))

    def test_startup_equals_resume(self, repo: Path):
        assert self._ctx(repo, "session_startup.json") == self._ctx(repo, "session_resume.json")

    def test_startup_equals_clear(self, repo: Path):
        assert self._ctx(repo, "session_startup.json") == self._ctx(repo, "session_clear.json")

    def test_startup_equals_compact(self, repo: Path):
        assert self._ctx(repo, "session_startup.json") == self._ctx(repo, "session_compact.json")


# ─────────────────────────────────────────────────────────────────────────────
# Double logging (.claude/logs/session-start.jsonl + phase-gates.jsonl)
# ─────────────────────────────────────────────────────────────────────────────


class TestLogging:
    def _read(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    def test_hook_log_written(self, repo: Path):
        run_hook(load_fixture("session_startup.json"), cwd=repo)
        entries = self._read(repo / ".claude" / "logs" / "session-start.jsonl")
        assert len(entries) == 1

    def test_phase_log_written(self, repo: Path):
        run_hook(load_fixture("session_startup.json"), cwd=repo)
        entries = self._read(repo / ".claude" / "logs" / "phase-gates.jsonl")
        assert len(entries) == 1

    def test_hook_log_entry_shape(self, repo: Path):
        checkout_feat(repo, "feat/d2-test")
        run_hook(load_fixture("session_startup.json"), cwd=repo)
        entries = self._read(repo / ".claude" / "logs" / "session-start.jsonl")
        e = entries[0]
        assert e["hook"] == "session-start"
        assert e["source"] == "startup"
        assert e["branch"] == "feat/d2-test"
        assert "phase" in e
        assert "warnings" in e
        assert "ts" in e

    def test_phase_log_event_shape(self, repo: Path):
        checkout_feat(repo, "feat/d2-test")
        run_hook(load_fixture("session_startup.json"), cwd=repo)
        entries = self._read(repo / ".claude" / "logs" / "phase-gates.jsonl")
        e = entries[0]
        assert e["event"] == "session_start"
        assert e["source"] == "startup"
        assert e["branch"] == "feat/d2-test"
        assert "ts" in e

    def test_source_recorded_in_logs(self, repo: Path):
        run_hook(load_fixture("session_compact.json"), cwd=repo)
        hook_log = self._read(repo / ".claude" / "logs" / "session-start.jsonl")
        phase_log = self._read(repo / ".claude" / "logs" / "phase-gates.jsonl")
        assert hook_log[0]["source"] == "compact"
        assert phase_log[0]["source"] == "compact"

    def test_logs_are_append_only(self, repo: Path):
        run_hook(load_fixture("session_startup.json"), cwd=repo)
        run_hook(load_fixture("session_resume.json"), cwd=repo)
        hook_log = self._read(repo / ".claude" / "logs" / "session-start.jsonl")
        phase_log = self._read(repo / ".claude" / "logs" / "phase-gates.jsonl")
        assert len(hook_log) == 2
        assert len(phase_log) == 2

    def test_log_dir_created_if_missing(self, tmp_path: Path):
        # skip the repo fixture — start from scratch without .claude/logs
        (tmp_path / ".claude" / "branch-approvals").mkdir(parents=True)
        git(tmp_path, "init", "-q", "-b", "main")
        (tmp_path / "README.md").write_text("x\n")
        git(tmp_path, "add", ".")
        git(tmp_path, "commit", "-q", "-m", "init")
        run_hook(load_fixture("session_startup.json"), cwd=tmp_path)
        assert (tmp_path / ".claude" / "logs" / "session-start.jsonl").exists()
        assert (tmp_path / ".claude" / "logs" / "phase-gates.jsonl").exists()


# ─────────────────────────────────────────────────────────────────────────────
# Safe-fail graceful (G: informative hooks degrade gracefully, exit 0)
# ─────────────────────────────────────────────────────────────────────────────


class TestSafeFailGraceful:
    def test_malformed_json_exits_zero(self, repo: Path):
        result = run_hook("this is not json {{{", cwd=repo)
        assert result.returncode == 0

    def test_empty_stdin_exits_zero(self, repo: Path):
        result = run_hook("", cwd=repo)
        assert result.returncode == 0

    def test_non_dict_top_level_exits_zero(self, repo: Path):
        result = run_hook("[1,2,3]", cwd=repo)
        assert result.returncode == 0

    def test_missing_source_does_not_crash(self, repo: Path):
        result = run_hook({"hook_event_name": "SessionStart"}, cwd=repo)
        assert result.returncode == 0

    def test_malformed_emits_additional_context(self, repo: Path):
        result = run_hook("garbage", cwd=repo)
        out = parse_stdout(result)
        assert "additionalContext" in out["hookSpecificOutput"]

    def test_malformed_logs_error_entry(self, repo: Path):
        run_hook("garbage", cwd=repo)
        log = repo / ".claude" / "logs" / "session-start.jsonl"
        entries = [json.loads(l) for l in log.read_text().splitlines() if l.strip()] if log.exists() else []
        assert any("error" in e for e in entries)

    def test_cwd_not_git_repo_does_not_crash(self, tmp_path: Path):
        # no git init → cwd is not a repo
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        result = run_hook(load_fixture("session_startup.json"), cwd=tmp_path)
        assert result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Last merge (git log --merges)
# ─────────────────────────────────────────────────────────────────────────────


class TestLastMerge:
    def test_no_merges_yet_shows_none(self, repo: Path):
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        # initial commit only, no merges
        last_merge_line = next(l for l in ctx.splitlines() if "Last merge" in l)
        assert "(none)" in last_merge_line

    def test_merge_commit_shown(self, repo: Path):
        git(repo, "checkout", "-q", "-b", "side")
        (repo / "x.md").write_text("x\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "side commit")
        git(repo, "checkout", "-q", "main")
        git(repo, "merge", "--no-ff", "-q", "side", "-m", "merge side into main")
        ctx = additional_context(run_hook(load_fixture("session_startup.json"), cwd=repo))
        assert "merge side into main" in ctx


# ─────────────────────────────────────────────────────────────────────────────
# In-process unit tests (coverage visibility, pure helpers)
# ─────────────────────────────────────────────────────────────────────────────


class TestDerivePhaseFromSlugUnit:
    def test_feat_d2(self):
        assert ss.phase_from_slug("feat/d2-hook-session-start") == "D2"

    def test_feat_d2_underscored(self):
        assert ss.phase_from_slug("feat_d2-hook-session-start") == "D2"

    def test_fix_c5(self):
        assert ss.phase_from_slug("fix/c5-tildes") == "C5"

    def test_chore_b1(self):
        assert ss.phase_from_slug("chore/b1-scaffold") == "B1"

    def test_refactor_e1(self):
        assert ss.phase_from_slug("refactor/e1-foo") == "E1"

    def test_no_prefix_returns_none(self):
        assert ss.phase_from_slug("feat/no-num-x") is None

    def test_unknown_kind_returns_none(self):
        assert ss.phase_from_slug("random/d2-x") is None

    def test_empty_returns_none(self):
        assert ss.phase_from_slug("") is None

    def test_two_digit_num(self):
        assert ss.phase_from_slug("feat/d12-foo") == "D12"


class TestMainInProcess:
    STARTUP = '{"hook_event_name":"SessionStart","session_id":"x","source":"startup"}'

    def _run(self, monkeypatch, repo: Path, stdin_text: str) -> int:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        return ss.main()

    def test_startup_on_main_returns_zero(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, self.STARTUP) == 0

    def test_malformed_returns_zero(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "not json") == 0

    def test_non_dict_returns_zero(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "[1,2]") == 0

    def test_empty_returns_zero(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "") == 0

    def test_feat_branch_warnings_path_in_process(self, monkeypatch, repo):
        checkout_feat(repo, "feat/d2-test")
        (repo / "some_code.py").write_text("pass\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "code only")
        assert self._run(monkeypatch, repo, self.STARTUP) == 0
        hook_log = repo / ".claude" / "logs" / "session-start.jsonl"
        entry = json.loads(hook_log.read_text().splitlines()[-1])
        assert entry["branch"] == "feat/d2-test"
        assert entry["phase"] == "D2"
        assert any("marker" in w for w in entry["warnings"])
        assert any("docs-sync" in w for w in entry["warnings"])

    def test_feat_with_docs_diff_no_docs_warning_in_process(self, monkeypatch, repo):
        (repo / "ROADMAP.md").write_text("# r\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "add roadmap")
        checkout_feat(repo, "feat/d2-test")
        place_marker(repo, "feat_d2-test")
        (repo / "ROADMAP.md").write_text("# r\n- x\n")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", "bump roadmap")
        assert self._run(monkeypatch, repo, self.STARTUP) == 0
        hook_log = repo / ".claude" / "logs" / "session-start.jsonl"
        entry = json.loads(hook_log.read_text().splitlines()[-1])
        assert entry["warnings"] == []

    def test_main_phase_fallback_in_process(self, monkeypatch, repo):
        seed_phase_log(repo, [
            {"ts": "2026-01-01T00:00:00Z", "event": "branch_creation", "slug": "feat_d1-x", "decision": "allow"},
        ])
        assert self._run(monkeypatch, repo, self.STARTUP) == 0
        hook_log = repo / ".claude" / "logs" / "session-start.jsonl"
        entry = json.loads(hook_log.read_text().splitlines()[-1])
        assert entry["phase"] == "D1"

    def test_non_git_cwd_in_process(self, monkeypatch, tmp_path):
        (tmp_path / ".claude" / "logs").mkdir(parents=True)
        assert self._run(monkeypatch, tmp_path, self.STARTUP) == 0
        hook_log = tmp_path / ".claude" / "logs" / "session-start.jsonl"
        entry = json.loads(hook_log.read_text().splitlines()[-1])
        assert entry["branch"] is None
        assert entry["phase"] == "unknown"
