"""Integration contract between .claude/skills/_shared/log-invocation.sh
(E1a) and hooks/stop-policy-check.py (D6 scaffold activated in E1a).

Purpose:
  - Lock the shape of `.claude/logs/skills.jsonl` entries emitted by the
    shared shell logger so `stop-policy-check._extract_invoked_skills` can
    read them. Shape fixed in E1a Fase -1: {ts, skill, session_id, status}.
    No extra fields (no args, no duration_ms) until a real need appears.
  - Exercise end-to-end enforcement: populate `skills_allowed`, emit one or
    more entries via the shell script, invoke the Stop hook with a matching
    session_id, assert allow/deny.
  - Best-effort framing: if the shell script isn't invoked (LLM skips the
    final step), `skills.jsonl` has no entry for that invocation — allow.
    No cryptographic guarantee is claimed.

D6 regression guard: tests in test_stop_policy_check.py continue to use the
`pos:*` placeholder names in fixtures. This file uses the REAL E1a names
(project-kickoff, writing-handoff) — it is the integration test for the
real names, not a fixture replica.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-policy-check.py"
LOGGER = REPO_ROOT / ".claude" / "skills" / "_shared" / "log-invocation.sh"

# Make `_lib` importable here explicitly, without relying on the hook
# module's sys.path mutation as a side effect of exec_module below.
sys.path.insert(0, str(REPO_ROOT / "hooks"))

# Import ALLOWED_SKILLS from the canonical location (shared skills tests module)
# to avoid duplication across test files.
SKILLS_TEST_DIR = REPO_ROOT / ".claude" / "skills" / "tests"
if str(SKILLS_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_TEST_DIR))
from _allowed_skills import ALLOWED_SKILLS  # noqa: E402

_spec = importlib.util.spec_from_file_location("stop_policy_check", HOOK)
assert _spec is not None and _spec.loader is not None
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


SESSION_ID = "test-session"  # matches hooks/tests/fixtures/payloads/stop.json


@pytest.fixture(autouse=True)
def clear_cache():
    from _lib import policy as pol
    pol.reset_cache()
    yield
    pol.reset_cache()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repo with `.claude/logs/` and no policy file (caller writes it)."""
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    return tmp_path


def write_skills_allowed(repo_dir: Path, allowed: list[str]) -> None:
    (repo_dir / "policy.yaml").write_text(
        yaml.safe_dump({"skills_allowed": allowed}, sort_keys=False),
        encoding="utf-8",
    )


def run_logger(repo_dir: Path, skill: str, session_id: str = SESSION_ID,
               status: str = "ok") -> subprocess.CompletedProcess:
    """Invoke the shell logger as a skill would. Env carries session id."""
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    return subprocess.run(
        [str(LOGGER), skill, status],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )


def run_stop_hook(repo_dir: Path, session_id: str = SESSION_ID) -> subprocess.CompletedProcess:
    payload = {"session_id": session_id, "hook_event_name": "Stop"}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=repo_dir,
        timeout=5,
    )


def read_skills_log(repo_dir: Path) -> list[dict]:
    log = repo_dir / ".claude" / "logs" / "skills.jsonl"
    if not log.exists():
        return []
    return [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ────────────────────────────────────────────────────────────────────────────
# Shape of skills.jsonl entries
# ────────────────────────────────────────────────────────────────────────────


class TestLoggerShape:
    def test_logger_emits_valid_jsonl_entry(self, repo: Path):
        result = run_logger(repo, "project-kickoff")
        assert result.returncode == 0, (
            f"logger exited non-zero: stderr={result.stderr!r}"
        )
        entries = read_skills_log(repo)
        assert len(entries) == 1
        entry = entries[0]
        assert set(entry) == {"ts", "skill", "session_id", "status"}, (
            f"Expected exactly 4 keys in skills.jsonl entry, got {set(entry)}"
        )
        assert entry["skill"] == "project-kickoff"
        assert entry["session_id"] == SESSION_ID
        assert entry["status"] == "ok"
        assert isinstance(entry["ts"], str) and entry["ts"]

    def test_logger_appends_not_overwrites(self, repo: Path):
        run_logger(repo, "project-kickoff")
        run_logger(repo, "writing-handoff")
        entries = read_skills_log(repo)
        assert [e["skill"] for e in entries] == [
            "project-kickoff",
            "writing-handoff",
        ]

    def test_logger_defaults_status_ok(self, repo: Path):
        """Calling with just a skill name (no status arg) must still emit
        status=ok — the shape is {ts, skill, session_id, status} always."""
        env = os.environ.copy()
        env["CLAUDE_SESSION_ID"] = SESSION_ID
        subprocess.run(
            [str(LOGGER), "project-kickoff"],
            cwd=repo, env=env, capture_output=True, text=True, timeout=5,
        )
        entries = read_skills_log(repo)
        assert len(entries) == 1
        assert entries[0]["status"] == "ok"

    def test_logger_creates_logs_dir_if_missing(self, tmp_path: Path):
        """A skill invocation in a fresh repo without `.claude/logs/` must
        still succeed (best-effort, never breaks the skill)."""
        # Deliberately DON'T create .claude/logs here.
        result = run_logger(tmp_path, "project-kickoff")
        assert result.returncode == 0
        assert (tmp_path / ".claude" / "logs" / "skills.jsonl").is_file()


# ────────────────────────────────────────────────────────────────────────────
# stop-policy-check._extract_invoked_skills can read the logger's output
# ────────────────────────────────────────────────────────────────────────────


class TestExtractorReadsLoggerOutput:
    def test_single_entry_readable(self, repo: Path):
        run_logger(repo, "project-kickoff")
        assert sp._extract_invoked_skills(repo, SESSION_ID) == ["project-kickoff"]

    def test_multi_entry_readable_in_order(self, repo: Path):
        run_logger(repo, "project-kickoff")
        run_logger(repo, "writing-handoff")
        assert sp._extract_invoked_skills(repo, SESSION_ID) == [
            "project-kickoff", "writing-handoff",
        ]

    def test_other_session_ignored(self, repo: Path):
        run_logger(repo, "project-kickoff", session_id="older-session")
        run_logger(repo, "writing-handoff", session_id=SESSION_ID)
        assert sp._extract_invoked_skills(repo, SESSION_ID) == ["writing-handoff"]


# ────────────────────────────────────────────────────────────────────────────
# End-to-end: logger + stop-policy-check with real E1a skill names
# ────────────────────────────────────────────────────────────────────────────


class TestEnforcementEndToEnd:
    def test_both_invocations_allowed_when_both_in_allowlist(self, repo: Path):
        write_skills_allowed(repo, ["project-kickoff", "writing-handoff"])
        run_logger(repo, "project-kickoff")
        run_logger(repo, "writing-handoff")
        result = run_stop_hook(repo)
        assert result.returncode == 0, (
            f"expected allow, got deny: stdout={result.stdout!r}"
        )

    def test_invocation_outside_allowlist_denies(self, repo: Path):
        write_skills_allowed(repo, ["project-kickoff"])
        run_logger(repo, "project-kickoff")
        run_logger(repo, "writing-handoff")  # not in allowlist
        result = run_stop_hook(repo)
        assert result.returncode == 2
        out = json.loads(result.stdout)
        reason = out["hookSpecificOutput"]["decisionReason"]
        assert "writing-handoff" in reason

    def test_no_invocations_allowed(self, repo: Path):
        """A Stop with zero skill invocations in the session must allow,
        even with a populated allowlist. Silence is not a violation."""
        write_skills_allowed(repo, ["project-kickoff", "writing-handoff"])
        result = run_stop_hook(repo)
        assert result.returncode == 0

    def test_skipped_log_entry_does_not_break_enforcement(self, repo: Path):
        """Best-effort framing: if the LLM skips the logger on one invocation,
        the entry is simply missing from skills.jsonl — enforcement silently
        allows (it can't know about what isn't logged). Never raises."""
        write_skills_allowed(repo, ["project-kickoff"])
        # No logger call at all — simulating LLM skipping the last step.
        result = run_stop_hook(repo)
        assert result.returncode == 0

    def test_all_thirteen_e1_e3b_skills_end_to_end(self, repo: Path):
        """E3b extends the allowlist to 13 entries (E1a+E1b+E2a+E2b+E3a+E3b).
        Emit one log line per skill via the shared logger, invoke Stop, expect
        allow. Guards against a typo in either the policy, the logger, or the
        Stop hook silently breaking the full 13-skill contract."""
        write_skills_allowed(repo, ALLOWED_SKILLS)
        for skill in ALLOWED_SKILLS:
            run_logger(repo, skill)
        result = run_stop_hook(repo)
        assert result.returncode == 0, (
            f"expected allow for all {len(ALLOWED_SKILLS)} E1a+E1b+E2a+E2b+E3a+E3b skills, "
            f"got deny: stdout={result.stdout!r}"
        )
