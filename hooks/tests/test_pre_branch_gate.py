"""Tests for hooks/pre-branch-gate.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "pre-branch-gate.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

TEST_SLUG = "feat/d1-test"
TEST_MARKER_NAME = "feat_d1-test.approved"


def run_hook(payload: dict | str, cwd: Path) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload) if isinstance(payload, dict) else payload
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
    )


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".claude" / "branch-approvals").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path


def place_marker(repo: Path, name: str = TEST_MARKER_NAME) -> None:
    (repo / ".claude" / "branch-approvals" / name).touch()


def parse_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)


class TestBranchCreationDetection:
    def test_checkout_b_with_marker_allows(self, repo: Path):
        place_marker(repo)
        result = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_checkout_b_without_marker_denies(self, repo: Path):
        result = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert result.returncode == 2
        out = parse_stdout(result)
        decision = out["hookSpecificOutput"]["permissionDecision"]
        reason = out["hookSpecificOutput"]["decisionReason"]
        assert decision == "deny"
        assert TEST_MARKER_NAME in reason
        assert "touch" in reason
        assert "MASTER_PLAN.md" in reason

    def test_switch_c_with_marker_allows(self, repo: Path):
        place_marker(repo)
        result = run_hook(load_fixture("switch_c.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_switch_c_without_marker_denies(self, repo: Path):
        result = run_hook(load_fixture("switch_c.json"), cwd=repo)
        assert result.returncode == 2

    def test_worktree_add_b_with_marker_allows(self, repo: Path):
        place_marker(repo)
        result = run_hook(load_fixture("worktree_add_b.json"), cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_worktree_add_b_without_marker_denies(self, repo: Path):
        result = run_hook(load_fixture("worktree_add_b.json"), cwd=repo)
        assert result.returncode == 2

    def test_git_with_global_options_before_subcommand_detected(self, repo: Path):
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git -c user.name=test checkout -b feat/d1-test"
            },
        }
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 2


class TestPassThrough:
    def test_git_status_silent(self, repo: Path):
        result = run_hook(load_fixture("git_status.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_git_branch_without_flag_silent(self, repo: Path):
        result = run_hook(load_fixture("git_branch_no_flag.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_non_bash_tool_silent(self, repo: Path):
        result = run_hook(load_fixture("non_bash.json"), cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_git_checkout_existing_branch_silent(self, repo: Path):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout main"},
        }
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestSlugSanitization:
    def test_slash_to_underscore(self, repo: Path):
        place_marker(repo, "feat_d1-test.approved")
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout -b feat/d1-test"},
        }
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0, result.stderr

    def test_deeply_nested_slug(self, repo: Path):
        place_marker(repo, "feat_x_y_z.approved")
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git switch -c feat/x/y/z"},
        }
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0, result.stderr


class TestLogging:
    def test_both_logs_written_on_deny(self, repo: Path):
        result = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert result.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-branch-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        entries = [
            json.loads(line)
            for line in hook_log.read_text().splitlines()
            if line.strip()
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["decision"] == "deny"
        assert entry["slug"] == "feat_d1-test"
        assert "ts" in entry
        assert "command" in entry
        assert "reason" in entry

    def test_both_logs_written_on_allow(self, repo: Path):
        place_marker(repo)
        result = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-branch-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert hook_log.exists()
        assert phase_log.exists()
        entries = [
            json.loads(line)
            for line in hook_log.read_text().splitlines()
            if line.strip()
        ]
        assert entries[-1]["decision"] == "allow"

    def test_phase_gates_event_shape(self, repo: Path):
        place_marker(repo)
        result = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert result.returncode == 0
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        entries = [
            json.loads(line)
            for line in phase_log.read_text().splitlines()
            if line.strip()
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["event"] == "branch_creation"
        assert entry["slug"] == "feat_d1-test"
        assert entry["decision"] == "allow"
        assert "ts" in entry

    def test_pass_through_does_not_log(self, repo: Path):
        result = run_hook(load_fixture("git_status.json"), cwd=repo)
        assert result.returncode == 0
        hook_log = repo / ".claude" / "logs" / "pre-branch-gate.jsonl"
        phase_log = repo / ".claude" / "logs" / "phase-gates.jsonl"
        assert not hook_log.exists()
        assert not phase_log.exists()


class TestRobustness:
    def test_malformed_stdin_denies(self, repo: Path):
        result = run_hook("this is not JSON{{{", cwd=repo)
        assert result.returncode == 2

    def test_empty_stdin_denies(self, repo: Path):
        result = run_hook("", cwd=repo)
        assert result.returncode == 2

    def test_missing_tool_input_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash"}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_missing_command_passes_through(self, repo: Path):
        payload = {"tool_name": "Bash", "tool_input": {}}
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_unparseable_command_passes_through(self, repo: Path):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout -b 'unterminated"},
        }
        result = run_hook(payload, cwd=repo)
        assert result.returncode == 0

    def test_idempotent_on_deny(self, repo: Path):
        r1 = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        r2 = run_hook(load_fixture("checkout_b.json"), cwd=repo)
        assert r1.returncode == r2.returncode == 2
        hook_log = repo / ".claude" / "logs" / "pre-branch-gate.jsonl"
        entries = [
            json.loads(line)
            for line in hook_log.read_text().splitlines()
            if line.strip()
        ]
        assert len(entries) == 2
        assert entries[0]["decision"] == entries[1]["decision"] == "deny"
