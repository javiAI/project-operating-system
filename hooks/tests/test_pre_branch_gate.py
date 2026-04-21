"""Tests for hooks/pre-branch-gate.py."""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "pre-branch-gate.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

_spec = importlib.util.spec_from_file_location("pre_branch_gate", HOOK)
assert _spec is not None and _spec.loader is not None
pbg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pbg)

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


class TestSanitizeSlugUnit:
    def test_no_slash(self):
        assert pbg.sanitize_slug("feat_x") == "feat_x"

    def test_single_slash(self):
        assert pbg.sanitize_slug("feat/x") == "feat_x"

    def test_multiple_slashes(self):
        assert pbg.sanitize_slug("feat/d1/x") == "feat_d1_x"


class TestExtractBranchSlugUnit:
    def test_checkout_b(self):
        assert pbg.extract_branch_slug("git checkout -b feat/x") == "feat/x"

    def test_switch_c(self):
        assert pbg.extract_branch_slug("git switch -c feat/x") == "feat/x"

    def test_worktree_add_b(self):
        assert pbg.extract_branch_slug("git worktree add -b feat/x /tmp/wt") == "feat/x"

    def test_checkout_existing_branch_none(self):
        assert pbg.extract_branch_slug("git checkout main") is None

    def test_status_none(self):
        assert pbg.extract_branch_slug("git status") is None

    def test_branch_without_flag_none(self):
        assert pbg.extract_branch_slug("git branch feat/x") is None

    def test_not_git_none(self):
        assert pbg.extract_branch_slug("ls -la") is None

    def test_unparseable_none(self):
        assert pbg.extract_branch_slug("git checkout -b 'unterminated") is None

    def test_empty_none(self):
        assert pbg.extract_branch_slug("") is None

    def test_git_only_none(self):
        assert pbg.extract_branch_slug("git") is None

    def test_only_global_opts_none(self):
        assert pbg.extract_branch_slug("git -c user.name=x") is None

    def test_global_opt_equals_form(self):
        assert pbg.extract_branch_slug("git --git-dir=/foo checkout -b feat/x") == "feat/x"

    def test_global_opt_space_form(self):
        assert pbg.extract_branch_slug("git -C /foo checkout -b feat/x") == "feat/x"

    def test_global_opt_paginate_no_arg(self):
        assert pbg.extract_branch_slug("git --no-pager checkout -b feat/x") == "feat/x"

    def test_global_opt_exec_path_space_form(self):
        assert pbg.extract_branch_slug("git --exec-path /foo checkout -b feat/x") == "feat/x"

    def test_global_opt_upload_pack_space_form(self):
        assert pbg.extract_branch_slug("git --upload-pack /foo checkout -b feat/x") == "feat/x"

    def test_checkout_b_no_arg_none(self):
        assert pbg.extract_branch_slug("git checkout -b") is None

    def test_switch_c_no_arg_none(self):
        assert pbg.extract_branch_slug("git switch -c") is None

    def test_worktree_add_no_b_none(self):
        assert pbg.extract_branch_slug("git worktree add /tmp/wt") is None

    def test_worktree_add_b_no_arg_none(self):
        assert pbg.extract_branch_slug("git worktree add -b") is None

    def test_worktree_list_none(self):
        assert pbg.extract_branch_slug("git worktree list") is None

    def test_unknown_subcmd_none(self):
        assert pbg.extract_branch_slug("git fetch origin") is None


class TestBuildDenyReasonUnit:
    def test_contains_marker_touch_and_plan(self):
        reason = pbg.build_deny_reason(
            Path("/repo/.claude/branch-approvals/feat_x.approved"),
            "git checkout -b feat/x",
        )
        assert "feat_x.approved" in reason
        assert "touch" in reason
        assert "MASTER_PLAN.md" in reason
        assert "git checkout -b feat/x" in reason


class TestMainInProcess:
    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        repo: Path,
        stdin_text: str,
    ) -> int:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
        return pbg.main()

    def test_malformed_json_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "not json") == 2

    def test_non_dict_payload_returns_2(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, "[1,2,3]") == 2

    def test_non_bash_returns_0(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, '{"tool_name": "Write"}') == 0

    def test_bash_no_tool_input_returns_0(self, monkeypatch, repo):
        assert self._run(monkeypatch, repo, '{"tool_name": "Bash"}') == 0

    def test_bash_empty_command_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": {"command": "   "}}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_bash_non_branch_returns_0(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": {"command": "ls"}}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_branch_with_marker_returns_0(self, monkeypatch, repo):
        (repo / ".claude" / "branch-approvals" / "feat_x.approved").touch()
        payload = '{"tool_name": "Bash", "tool_input": {"command": "git checkout -b feat/x"}}'
        assert self._run(monkeypatch, repo, payload) == 0

    def test_branch_without_marker_returns_2(self, monkeypatch, repo):
        payload = '{"tool_name": "Bash", "tool_input": {"command": "git checkout -b feat/x"}}'
        assert self._run(monkeypatch, repo, payload) == 2
