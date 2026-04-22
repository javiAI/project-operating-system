"""Tests for hooks/post-action.py.

D5 PostToolUse(Bash) hook — non-blocking, exit 0 always. Detects relevant
local merges via hierarchical strategy and emits additionalContext suggesting
`/pos:compound` when hardcoded mirror of
`policy.yaml.lifecycle.post_merge.skills_conditional[0].trigger` matches.

Crystal-clear contract this suite locks in:

Tier 1 (command-based primary signal) — matches:
    - `git merge <ref>`         (A)
    - `git pull` without --rebase (C)
Tier 1 — explicitly NOT matched (pass-through silent):
    - `git merge --abort | --quit | --continue | --skip`
    - `git pull --rebase ...`
    - `gh pr merge ...`          (B removed; local state unchanged)
    - `git rebase ...`, `git cherry-pick ...`, `git status`, etc.

Tier 2 (reflog post-hoc confirmation) — required for A and C:
    - A: `git reflog HEAD -1 --format=%gs` starts with "merge ".
    - C: `... --format=%gs` starts with "pull:" (or "pull " w/o "--rebase").
Tier 2 failure → status "tier2_unconfirmed" (hook log only, phase-gates intact).

Touched paths derivation (A + C):
    `git diff --name-only HEAD@{1} HEAD`.
    None → "diff_unavailable" (hook log only).
    []   → "confirmed_no_triggers" (both logs, no additionalContext).

Policy mirror (hardcoded; literal of policy.yaml L105-120):
    trigger.touched_paths_any_of: generator/lib/** | generator/renderers/** |
                                  hooks/** | skills/** | templates/**/*.hbs
    trigger.skip_if_only: docs/** | *.md | .claude/patterns/**
    trigger.min_files_changed: 2

Emission rules (all four must hold for additionalContext):
    1. Tier 1 matches.
    2. Tier 2 confirms.
    3. touched_paths non-empty AND len >= MIN_FILES_CHANGED (2).
    4. NOT (all touched paths match skip_if_only).
    5. At least one path matches a TRIGGER_GLOBS entry.

Exit code: always 0 (non-blocking PostToolUse).
Safe-fail: malformed stdin / JSON / types → exit 0, no log, no output.

Shape emparentado con D1 blocker (shlex, hook log + phase-gates.jsonl,
importlib in-process for coverage), pero PostToolUse no-blocking — NO emite
permissionDecision bajo ningún camino.
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "post-action.py"
FIXTURES = Path(__file__).parent / "fixtures" / "payloads"

_HOOK_EXISTS = HOOK.exists()
if _HOOK_EXISTS:
    _spec = importlib.util.spec_from_file_location("post_action", HOOK)
    assert _spec is not None and _spec.loader is not None
    pa = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(pa)
else:
    pa = None


needs_hook = pytest.mark.skipif(
    not _HOOK_EXISTS, reason="hook not yet implemented (RED kickoff state)"
)


# ---------------------------------------------------------------------------
# test helpers
# ---------------------------------------------------------------------------


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


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


def parse_stdout(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)


def make_bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


POLICY_YAML_FOR_TESTS = """\
lifecycle:
  post_merge:
    skills_conditional:
      - skill: "pos:compound"
        trigger:
          touched_paths_any_of:
            - "generator/lib/**"
            - "generator/renderers/**"
            - "hooks/**"
            - "skills/**"
            - "templates/**/*.hbs"
          skip_if_only:
            - "docs/**"
            - "*.md"
            - ".claude/patterns/**"
          min_files_changed: 2
"""


def _write_policy(root: Path) -> None:
    (root / "policy.yaml").write_text(POLICY_YAML_FOR_TESTS)


def _test_trigger():
    """PostMergeTrigger instance mirroring POLICY_YAML_FOR_TESTS."""
    sys.path.insert(0, str(REPO_ROOT / "hooks"))
    from _lib.policy import PostMergeTrigger
    return PostMergeTrigger(
        touched_paths_any_of=(
            "generator/lib/**",
            "generator/renderers/**",
            "hooks/**",
            "skills/**",
            "templates/**/*.hbs",
        ),
        skip_if_only=("docs/**", "*.md", ".claude/patterns/**"),
        min_files_changed=2,
    )


@pytest.fixture(autouse=True)
def _reset_policy_cache():
    hooks_path = str(REPO_ROOT / "hooks")
    added = hooks_path not in sys.path
    if added:
        sys.path.insert(0, hooks_path)
    from _lib.policy import reset_cache
    reset_cache()
    try:
        yield
    finally:
        reset_cache()
        if added:
            try:
                sys.path.remove(hooks_path)
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# fixtures — real git repos with controlled reflog state
# ---------------------------------------------------------------------------


@pytest.fixture
def repo_after_merge(tmp_path: Path) -> Path:
    """Repo where a `git merge` just ran — reflog entry starts with 'merge '.

    Topology: main has initial commit. feat/x branches off and adds 2 files
    (hooks/foo.py + skills/bar/SKILL.md). Merge back into main with --no-ff
    so reflog picks up "merge feat/x: Merge made by the 'ort' strategy".
    touched_paths(HEAD@{1}..HEAD) = the 2 files.
    """
    _git(tmp_path, "init", "-q", "--initial-branch=main")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "README.md").write_text("init\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "checkout", "-q", "-b", "feat/x")
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "foo.py").write_text("x\n")
    (tmp_path / "skills" / "bar").mkdir(parents=True)
    (tmp_path / "skills" / "bar" / "SKILL.md").write_text("x\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "feat")
    _git(tmp_path, "checkout", "-q", "main")
    _git(tmp_path, "merge", "--no-ff", "-q", "-m", "merge feat/x", "feat/x")
    (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
    _write_policy(tmp_path)
    return tmp_path


@pytest.fixture
def repo_after_merge_ff(tmp_path: Path) -> Path:
    """Repo where a fast-forward `git merge` just ran — reflog 'merge ...: Fast-forward'."""
    _git(tmp_path, "init", "-q", "--initial-branch=main")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "README.md").write_text("init\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "checkout", "-q", "-b", "feat/x")
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "foo.py").write_text("x\n")
    (tmp_path / "hooks" / "bar.py").write_text("y\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "feat")
    _git(tmp_path, "checkout", "-q", "main")
    _git(tmp_path, "merge", "--ff-only", "-q", "feat/x")
    (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
    _write_policy(tmp_path)
    return tmp_path


@pytest.fixture
def repo_after_pull(tmp_path: Path) -> Path:
    """Repo where `git pull` just ran — reflog entry starts with 'pull:'.

    Two-repo topology: upstream has an extra commit; clone pulls it.
    Touched path in the pull: hooks/pulled.py + templates/x/a.hbs.
    """
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "-q", "--bare", "--initial-branch=main")

    src = tmp_path / "src"
    src.mkdir()
    _git(src, "init", "-q", "--initial-branch=main")
    _git(src, "config", "user.email", "t@e.com")
    _git(src, "config", "user.name", "T")
    (src / "README.md").write_text("init\n")
    _git(src, "add", "README.md")
    _git(src, "commit", "-q", "-m", "init")
    _git(src, "remote", "add", "origin", str(upstream))
    _git(src, "push", "-q", "origin", "main")

    local = tmp_path / "local"
    _git(tmp_path, "clone", "-q", str(upstream), str(local))
    _git(local, "config", "user.email", "t@e.com")
    _git(local, "config", "user.name", "T")

    # upstream moves forward (touches hooks/** and templates/**)
    (src / "hooks").mkdir()
    (src / "hooks" / "pulled.py").write_text("p\n")
    (src / "templates" / "x").mkdir(parents=True)
    (src / "templates" / "x" / "a.hbs").write_text("t\n")
    _git(src, "add", "-A")
    _git(src, "commit", "-q", "-m", "upstream add")
    _git(src, "push", "-q", "origin", "main")

    # local pulls → reflog "pull: Fast-forward"
    _git(local, "pull", "-q")
    (local / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
    _write_policy(local)
    return local


@pytest.fixture
def repo_clean(tmp_path: Path) -> Path:
    """Repo with a single initial commit; no merge/pull in reflog."""
    _git(tmp_path, "init", "-q", "--initial-branch=main")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "README.md").write_text("init\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-q", "-m", "init")
    (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
    _write_policy(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# TestMatcherDetection — Tier 1 (command-based)
# ---------------------------------------------------------------------------


@needs_hook
class TestMatcherDetection:
    def test_git_merge_is_matcher_A(self):
        assert pa.classify_command("git merge origin/main") == "git_merge"

    def test_git_merge_no_ff_is_matcher_A(self):
        assert pa.classify_command("git merge --no-ff feat/x") == "git_merge"

    def test_git_merge_ff_only_is_matcher_A(self):
        assert pa.classify_command("git merge --ff-only feat/x") == "git_merge"

    def test_git_merge_abort_not_matched(self):
        assert pa.classify_command("git merge --abort") is None

    def test_git_merge_quit_not_matched(self):
        assert pa.classify_command("git merge --quit") is None

    def test_git_merge_continue_not_matched(self):
        assert pa.classify_command("git merge --continue") is None

    def test_git_merge_skip_not_matched(self):
        assert pa.classify_command("git merge --skip") is None

    def test_git_pull_is_matcher_C(self):
        assert pa.classify_command("git pull origin main") == "git_pull"

    def test_git_pull_no_args_is_matcher_C(self):
        assert pa.classify_command("git pull") == "git_pull"

    def test_git_pull_ff_only_is_matcher_C(self):
        assert pa.classify_command("git pull --ff-only") == "git_pull"

    def test_git_pull_rebase_not_matched(self):
        assert pa.classify_command("git pull --rebase origin main") is None

    def test_git_pull_rebase_shorthand_not_matched(self):
        assert pa.classify_command("git pull -r") is None

    def test_gh_pr_merge_not_matched(self):
        """B excluded: `tool_response.exit_code` not guaranteed in PostToolUse."""
        assert pa.classify_command("gh pr merge --squash") is None

    def test_gh_pr_merge_with_delete_not_matched(self):
        assert pa.classify_command("gh pr merge --squash --delete-branch") is None

    def test_git_rebase_not_matched(self):
        assert pa.classify_command("git rebase main") is None

    def test_git_cherry_pick_not_matched(self):
        assert pa.classify_command("git cherry-pick HEAD~1") is None

    def test_git_status_not_matched(self):
        assert pa.classify_command("git status") is None

    def test_git_push_not_matched(self):
        assert pa.classify_command("git push origin HEAD") is None

    def test_empty_string_not_matched(self):
        assert pa.classify_command("") is None

    def test_shlex_unparsable_not_matched(self):
        assert pa.classify_command('git merge "unclosed') is None

    def test_leading_whitespace_still_matched(self):
        assert pa.classify_command("  git merge feat/x  ") == "git_merge"


# ---------------------------------------------------------------------------
# TestTier2Reflog — post-hoc reflog confirmation
# ---------------------------------------------------------------------------


@needs_hook
class TestTier2Reflog:
    def test_reflog_after_real_merge_starts_with_merge(self, repo_after_merge: Path):
        msg = pa.reflog_message(repo_after_merge)
        assert msg is not None
        assert msg.startswith("merge ")

    def test_reflog_after_ff_merge_starts_with_merge(self, repo_after_merge_ff: Path):
        msg = pa.reflog_message(repo_after_merge_ff)
        assert msg is not None
        assert msg.startswith("merge ")

    def test_reflog_after_real_pull_starts_with_pull(self, repo_after_pull: Path):
        msg = pa.reflog_message(repo_after_pull)
        assert msg is not None
        assert msg.startswith("pull")

    def test_reflog_confirms_merge_for_merge_kind(self):
        assert pa.reflog_confirms("git_merge", "merge feat/x: Fast-forward") is True

    def test_reflog_confirms_merge_message_true_merge(self):
        assert pa.reflog_confirms("git_merge", "merge feat/x: Merge made by the 'ort' strategy.") is True

    def test_reflog_rejects_merge_when_msg_is_pull(self):
        assert pa.reflog_confirms("git_merge", "pull: Fast-forward") is False

    def test_reflog_confirms_pull_with_colon(self):
        assert pa.reflog_confirms("git_pull", "pull: Fast-forward") is True

    def test_reflog_confirms_pull_merge_made(self):
        assert pa.reflog_confirms("git_pull", "pull: Merge made by the 'ort' strategy.") is True

    def test_reflog_rejects_pull_rebase(self):
        assert pa.reflog_confirms("git_pull", "pull --rebase (start): checkout") is False

    def test_reflog_rejects_pull_when_msg_is_merge(self):
        assert pa.reflog_confirms("git_pull", "merge feat/x: Fast-forward") is False

    def test_reflog_rejects_none(self):
        assert pa.reflog_confirms("git_merge", None) is False
        assert pa.reflog_confirms("git_pull", None) is False

    def test_reflog_rejects_empty(self):
        assert pa.reflog_confirms("git_merge", "") is False

    def test_reflog_unknown_kind_rejected(self):
        assert pa.reflog_confirms("unknown_kind", "merge feat/x") is False

    def test_reflog_message_none_when_git_unavailable(self, tmp_path: Path):
        """Not a git repo → git reflog fails → None."""
        (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
        assert pa.reflog_message(tmp_path) is None

    def test_reflog_message_none_on_clean_repo_single_commit(self, repo_clean: Path):
        """Single-commit repo reflog has one entry ('commit (initial): init').
        The message exists and is non-empty; reflog_confirms must then reject
        it for both merge and pull kinds.
        """
        msg = pa.reflog_message(repo_clean)
        assert msg is not None
        assert not pa.reflog_confirms("git_merge", msg)
        assert not pa.reflog_confirms("git_pull", msg)


# ---------------------------------------------------------------------------
# TestTouchedPaths — git diff HEAD@{1} HEAD
# ---------------------------------------------------------------------------


@needs_hook
class TestTouchedPaths:
    def test_after_merge_returns_touched_files(self, repo_after_merge: Path):
        paths = pa.touched_paths(repo_after_merge)
        assert paths is not None
        assert "hooks/foo.py" in paths
        assert "skills/bar/SKILL.md" in paths

    def test_after_ff_merge_returns_touched_files(self, repo_after_merge_ff: Path):
        paths = pa.touched_paths(repo_after_merge_ff)
        assert paths is not None
        assert set(paths) == {"hooks/foo.py", "hooks/bar.py"}

    def test_after_pull_returns_touched_files(self, repo_after_pull: Path):
        paths = pa.touched_paths(repo_after_pull)
        assert paths is not None
        assert "hooks/pulled.py" in paths
        assert "templates/x/a.hbs" in paths

    def test_returns_none_when_no_prior_ref(self, repo_clean: Path):
        """Clean repo with 1 commit — HEAD@{1} doesn't resolve → None."""
        assert pa.touched_paths(repo_clean) is None

    def test_returns_none_when_not_a_repo(self, tmp_path: Path):
        assert pa.touched_paths(tmp_path) is None


# ---------------------------------------------------------------------------
# TestPolicyTriggers — hardcoded mirror of policy.yaml L105-120
# ---------------------------------------------------------------------------


@needs_hook
class TestMatchTriggers:
    def test_single_file_below_min_returns_empty(self):
        """1 file < min_files_changed=2 → no match."""
        assert pa.match_triggers(["hooks/foo.py"], _test_trigger()) == []

    def test_two_hooks_files_match_hooks_glob(self):
        assert pa.match_triggers(["hooks/a.py", "hooks/b.py"], _test_trigger()) == ["hooks/**"]

    def test_two_files_in_different_triggers_match_both(self):
        matched = pa.match_triggers(["hooks/a.py", "skills/x/SKILL.md"], _test_trigger())
        assert matched == ["hooks/**", "skills/**"]

    def test_generator_lib_matches(self):
        matched = pa.match_triggers(
            ["generator/lib/a.ts", "generator/lib/b.ts"], _test_trigger(),
        )
        assert matched == ["generator/lib/**"]

    def test_generator_renderers_matches(self):
        matched = pa.match_triggers(
            ["generator/renderers/a.ts", "generator/renderers/b.ts"], _test_trigger(),
        )
        assert matched == ["generator/renderers/**"]

    def test_templates_hbs_nested_matches(self):
        """Policy glob is `templates/**/*.hbs` — requires subdir."""
        matched = pa.match_triggers(
            ["templates/profile/a.hbs", "templates/profile/b.hbs"], _test_trigger(),
        )
        assert matched == ["templates/**/*.hbs"]

    def test_all_skip_only_returns_empty(self):
        """All paths in skip_if_only → compound should not fire."""
        assert pa.match_triggers(["docs/X.md", "docs/Y.md"], _test_trigger()) == []

    def test_only_root_md_files_skip_only(self):
        assert pa.match_triggers(["ROADMAP.md", "HANDOFF.md"], _test_trigger()) == []

    def test_only_patterns_skip_only(self):
        assert pa.match_triggers(
            [".claude/patterns/a.md", ".claude/patterns/b.md"], _test_trigger(),
        ) == []

    def test_mixed_skip_and_trigger_matches(self):
        """2 files: 1 doc + 1 hook → not all skip_if_only → fires on hooks/**."""
        matched = pa.match_triggers(["docs/X.md", "hooks/foo.py"], _test_trigger())
        assert matched == ["hooks/**"]

    def test_empty_list_returns_empty(self):
        assert pa.match_triggers([], _test_trigger()) == []

    def test_unrelated_paths_return_empty_even_with_min_met(self):
        """2 files but none match any trigger glob → empty."""
        assert pa.match_triggers(["scripts/deploy.sh", "Makefile"], _test_trigger()) == []

    def test_three_triggers_matched_ordering_follows_policy_list(self):
        matched = pa.match_triggers(
            ["skills/x.md", "hooks/foo.py", "generator/lib/bar.ts"], _test_trigger(),
        )
        assert matched == ["generator/lib/**", "hooks/**", "skills/**"]

    def test_matched_list_deduplicated(self):
        """Two hooks/ files → hooks/** appears once."""
        matched = pa.match_triggers(
            ["hooks/a.py", "hooks/b.py", "hooks/c.py"], _test_trigger(),
        )
        assert matched == ["hooks/**"]

    def test_templates_without_subdir_does_not_match(self):
        """`templates/**/*.hbs` requires at least one subdir between templates and file."""
        matched = pa.match_triggers(
            ["templates/a.hbs", "templates/b.hbs"], _test_trigger(),
        )
        assert matched == []


# ---------------------------------------------------------------------------
# TestIntegration — end-to-end via subprocess
# ---------------------------------------------------------------------------


class TestIntegrationMergeTriggersMatch:
    def test_merge_with_hooks_and_skills_emits_additional_context(
        self, repo_after_merge: Path,
    ):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        assert result.returncode == 0
        out = parse_stdout(result)
        hso = out["hookSpecificOutput"]
        assert hso["hookEventName"] == "PostToolUse"
        ctx = hso["additionalContext"]
        assert "compound" in ctx.lower()
        assert "/pos:compound" in ctx
        assert "hooks/**" in ctx
        assert "skills/**" in ctx

    def test_merge_writes_hook_log_confirmed_triggers_matched(
        self, repo_after_merge: Path,
    ):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        assert any(
            e.get("hook") == "post-action"
            and e.get("status") == "confirmed_triggers_matched"
            for e in entries
        )

    def test_merge_writes_phase_gates_post_merge_event(
        self, repo_after_merge: Path,
    ):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        phase = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "phase-gates.jsonl"
        )
        assert phase[-1]["event"] == "post_merge"
        assert "ts" in phase[-1]

    def test_merge_log_contains_triggers_matched_field(
        self, repo_after_merge: Path,
    ):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        confirmed = next(
            e for e in entries
            if e.get("status") == "confirmed_triggers_matched"
        )
        assert set(confirmed["triggers_matched"]) >= {"hooks/**", "skills/**"}
        assert set(confirmed["touched_paths"]) >= {
            "hooks/foo.py", "skills/bar/SKILL.md",
        }
        assert confirmed["kind"] == "git_merge"


class TestIntegrationPullTriggersMatch:
    def test_pull_emits_additional_context(self, repo_after_pull: Path):
        result = run_hook(load_fixture("git_pull.json"), cwd=repo_after_pull)
        assert result.returncode == 0
        out = parse_stdout(result)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "/pos:compound" in ctx
        assert "hooks/**" in ctx

    def test_pull_writes_post_merge_phase_event(self, repo_after_pull: Path):
        run_hook(load_fixture("git_pull.json"), cwd=repo_after_pull)
        phase = _read_jsonl(
            repo_after_pull / ".claude" / "logs" / "phase-gates.jsonl"
        )
        assert phase[-1]["event"] == "post_merge"

    def test_pull_log_records_kind_git_pull(self, repo_after_pull: Path):
        run_hook(load_fixture("git_pull.json"), cwd=repo_after_pull)
        entries = _read_jsonl(
            repo_after_pull / ".claude" / "logs" / "post-action.jsonl"
        )
        confirmed = next(
            e for e in entries
            if e.get("status") == "confirmed_triggers_matched"
        )
        assert confirmed["kind"] == "git_pull"


class TestIntegrationMergeFF:
    def test_ff_merge_emits_additional_context(self, repo_after_merge_ff: Path):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge_ff)
        assert result.returncode == 0
        out = parse_stdout(result)
        assert "additionalContext" in out["hookSpecificOutput"]


class TestIntegrationTier2Unconfirmed:
    def test_git_merge_command_on_clean_repo_logs_tier2_unconfirmed(
        self, repo_clean: Path,
    ):
        """Command matches git_merge but reflog is single-entry initial commit
        → Tier 2 fails → status 'tier2_unconfirmed', no additionalContext,
        no phase-gates entry."""
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""  # no additionalContext
        entries = _read_jsonl(
            repo_clean / ".claude" / "logs" / "post-action.jsonl"
        )
        assert any(e.get("status") == "tier2_unconfirmed" for e in entries)
        assert not (repo_clean / ".claude" / "logs" / "phase-gates.jsonl").exists()

    def test_git_pull_command_on_repo_with_merge_reflog_tier2_unconfirmed(
        self, repo_after_merge: Path,
    ):
        """Command is git_pull but reflog says 'merge ...' → Tier 2 rejects."""
        result = run_hook(load_fixture("git_pull.json"), cwd=repo_after_merge)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        assert any(e.get("status") == "tier2_unconfirmed" for e in entries)


class TestIntegrationConfirmedNoTriggers:
    def test_merge_of_only_docs_yields_confirmed_no_triggers(self, tmp_path: Path):
        """Merge touching only docs/** + *.md → all skip_if_only → no trigger."""
        _git(tmp_path, "init", "-q", "--initial-branch=main")
        _git(tmp_path, "config", "user.email", "t@e.com")
        _git(tmp_path, "config", "user.name", "T")
        (tmp_path / "README.md").write_text("x\n")
        _git(tmp_path, "add", "README.md")
        _git(tmp_path, "commit", "-q", "-m", "init")
        _git(tmp_path, "checkout", "-q", "-b", "feat/docs")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "A.md").write_text("a\n")
        (tmp_path / "docs" / "B.md").write_text("b\n")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "-m", "docs only")
        _git(tmp_path, "checkout", "-q", "main")
        _git(tmp_path, "merge", "--no-ff", "-q", "-m", "merge docs", "feat/docs")
        (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
        _write_policy(tmp_path)

        result = run_hook(load_fixture("git_merge.json"), cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == ""  # no additionalContext
        entries = _read_jsonl(tmp_path / ".claude" / "logs" / "post-action.jsonl")
        assert any(e.get("status") == "confirmed_no_triggers" for e in entries)
        phase = _read_jsonl(tmp_path / ".claude" / "logs" / "phase-gates.jsonl")
        assert phase[-1]["event"] == "post_merge"

    def test_merge_of_single_file_fails_min_files_changed(self, tmp_path: Path):
        """Single file in trigger glob — MIN_FILES_CHANGED=2 rejects."""
        _git(tmp_path, "init", "-q", "--initial-branch=main")
        _git(tmp_path, "config", "user.email", "t@e.com")
        _git(tmp_path, "config", "user.name", "T")
        (tmp_path / "README.md").write_text("x\n")
        _git(tmp_path, "add", "README.md")
        _git(tmp_path, "commit", "-q", "-m", "init")
        _git(tmp_path, "checkout", "-q", "-b", "feat/one")
        (tmp_path / "hooks").mkdir()
        (tmp_path / "hooks" / "only.py").write_text("x\n")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "-m", "one file")
        _git(tmp_path, "checkout", "-q", "main")
        _git(tmp_path, "merge", "--no-ff", "-q", "-m", "merge one", "feat/one")
        (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
        _write_policy(tmp_path)

        result = run_hook(load_fixture("git_merge.json"), cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        entries = _read_jsonl(tmp_path / ".claude" / "logs" / "post-action.jsonl")
        assert any(e.get("status") == "confirmed_no_triggers" for e in entries)


class TestIntegrationDiffUnavailable:
    def test_diff_unavailable_logs_status(self, monkeypatch, repo_after_merge: Path):
        """touched_paths returns None → status 'diff_unavailable', no phase entry."""
        import os
        # Force diff failure by stubbing the function via env — simpler: delete
        # .git/refs/remotes won't help; use a monkeypatched in-process run.
        # Use run_hook but sabotage HEAD@{1} resolution by deleting reflog AFTER capturing it.
        # Cleaner: monkeypatch pa.touched_paths at in-process level via TestMainInProcess.
        # Here we validate the shape via a synthesized run: remove .git directory
        # after Tier 2 query? Not feasible without deep mocking.
        # Skip: this behavior is covered by TestMainInProcess below.
        pytest.skip("covered by TestMainInProcess.test_main_diff_unavailable_logs_status")


# ---------------------------------------------------------------------------
# TestNonMatcherPassthrough — commands that don't match either matcher
# ---------------------------------------------------------------------------


class TestNonMatcherPassthrough:
    def test_gh_pr_merge_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("gh_pr_merge.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()
        assert not (repo_clean / ".claude" / "logs" / "phase-gates.jsonl").exists()

    def test_git_rebase_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("git_rebase.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_git_pull_rebase_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("git_pull_rebase.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_git_merge_abort_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("git_merge_abort.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_git_status_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("git_status.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_non_bash_passes_through_silent(self, repo_clean: Path):
        result = run_hook(load_fixture("non_bash.json"), cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()


# ---------------------------------------------------------------------------
# TestSafeFail — PostToolUse non-blocking safe-fail (always exit 0)
# ---------------------------------------------------------------------------


class TestSafeFail:
    def test_empty_stdin_exits_zero_no_output(self, repo_clean: Path):
        result = run_hook("", cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_malformed_json_exits_zero_no_output(self, repo_clean: Path):
        result = run_hook("not-json{", cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert not (repo_clean / ".claude" / "logs" / "post-action.jsonl").exists()

    def test_top_level_list_exits_zero(self, repo_clean: Path):
        result = run_hook("[]", cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_top_level_string_exits_zero(self, repo_clean: Path):
        result = run_hook('"str"', cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_missing_tool_name_exits_zero(self, repo_clean: Path):
        result = run_hook({"tool_input": {"command": "git merge"}}, cwd=repo_clean)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_non_bash_tool_name_exits_zero(self, repo_clean: Path):
        result = run_hook(
            {"tool_name": "Write", "tool_input": {"command": "git merge"}},
            cwd=repo_clean,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_tool_input_not_dict_exits_zero(self, repo_clean: Path):
        result = run_hook(
            {"tool_name": "Bash", "tool_input": "not-a-dict"},
            cwd=repo_clean,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_command_not_string_exits_zero(self, repo_clean: Path):
        result = run_hook(
            {"tool_name": "Bash", "tool_input": {"command": 42}},
            cwd=repo_clean,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_command_empty_exits_zero(self, repo_clean: Path):
        result = run_hook(
            {"tool_name": "Bash", "tool_input": {"command": "   "}},
            cwd=repo_clean,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_shlex_unparsable_command_passes_silent(self, repo_clean: Path):
        result = run_hook(
            {"tool_name": "Bash", "tool_input": {"command": 'git merge "unclosed'}},
            cwd=repo_clean,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# TestAdditionalContextShape
# ---------------------------------------------------------------------------


class TestAdditionalContextShape:
    def test_additional_context_mentions_pos_compound(
        self, repo_after_merge: Path,
    ):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        ctx = parse_stdout(result)["hookSpecificOutput"]["additionalContext"]
        assert "/pos:compound" in ctx

    def test_additional_context_mentions_post_merge_event(
        self, repo_after_merge: Path,
    ):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        ctx = parse_stdout(result)["hookSpecificOutput"]["additionalContext"]
        assert "post_merge" in ctx or "compound" in ctx.lower()

    def test_additional_context_lists_triggers_matched(
        self, repo_after_merge: Path,
    ):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        ctx = parse_stdout(result)["hookSpecificOutput"]["additionalContext"]
        assert "hooks/**" in ctx
        assert "skills/**" in ctx

    def test_additional_context_lists_touched_paths(
        self, repo_after_merge: Path,
    ):
        result = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        ctx = parse_stdout(result)["hookSpecificOutput"]["additionalContext"]
        assert "hooks/foo.py" in ctx or "skills/bar/SKILL.md" in ctx

    def test_touched_paths_capped_at_3_with_overflow_notice(self, tmp_path: Path):
        """More than 3 triggering files → additionalContext caps list and shows '+N more'."""
        _git(tmp_path, "init", "-q", "--initial-branch=main")
        _git(tmp_path, "config", "user.email", "t@e.com")
        _git(tmp_path, "config", "user.name", "T")
        (tmp_path / "README.md").write_text("x\n")
        _git(tmp_path, "add", "README.md")
        _git(tmp_path, "commit", "-q", "-m", "init")
        _git(tmp_path, "checkout", "-q", "-b", "feat/many")
        (tmp_path / "hooks").mkdir()
        for i in range(5):
            (tmp_path / "hooks" / f"f{i}.py").write_text("x\n")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "-m", "many")
        _git(tmp_path, "checkout", "-q", "main")
        _git(tmp_path, "merge", "--no-ff", "-q", "-m", "merge many", "feat/many")
        (tmp_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
        _write_policy(tmp_path)

        result = run_hook(load_fixture("git_merge.json"), cwd=tmp_path)
        ctx = parse_stdout(result)["hookSpecificOutput"]["additionalContext"]
        assert "more" in ctx.lower()


# ---------------------------------------------------------------------------
# TestMainInProcess — coverage + fine-grained mocks on pa.main()
# ---------------------------------------------------------------------------


@needs_hook
class TestMainInProcess:
    """Covers main() branches that subprocess can't easily exercise (git
    subprocess failures, exception paths, etc.). Uses monkeypatch to stub
    repo state instead of staging real git ops."""

    def _set_stdin(self, monkeypatch, payload: dict | str) -> None:
        data = json.dumps(payload) if isinstance(payload, dict) else payload
        monkeypatch.setattr(sys, "stdin", io.StringIO(data))

    def _cd(self, monkeypatch, path: Path) -> None:
        monkeypatch.chdir(path)

    def test_main_non_bash_returns_zero(self, monkeypatch, repo_clean: Path):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {}})
        assert pa.main() == 0

    def test_main_empty_stdin_returns_zero(self, monkeypatch, repo_clean: Path):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, "")
        assert pa.main() == 0

    def test_main_malformed_json_returns_zero(self, monkeypatch, repo_clean: Path):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, "{not-json")
        assert pa.main() == 0

    def test_main_top_level_list_returns_zero(self, monkeypatch, repo_clean: Path):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, "[]")
        assert pa.main() == 0

    def test_main_tool_input_not_dict_returns_zero(
        self, monkeypatch, repo_clean: Path,
    ):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, {"tool_name": "Bash", "tool_input": 123})
        assert pa.main() == 0

    def test_main_command_absent_returns_zero(
        self, monkeypatch, repo_clean: Path,
    ):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, {"tool_name": "Bash", "tool_input": {}})
        assert pa.main() == 0

    def test_main_non_matcher_returns_zero(
        self, monkeypatch, repo_clean: Path,
    ):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, make_bash("git status"))
        assert pa.main() == 0

    def test_main_git_merge_on_clean_repo_tier2_unconfirmed(
        self, monkeypatch, repo_clean: Path, capsys,
    ):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, make_bash("git merge feat/x"))
        rc = pa.main()
        assert rc == 0
        entries = _read_jsonl(repo_clean / ".claude" / "logs" / "post-action.jsonl")
        assert any(e.get("status") == "tier2_unconfirmed" for e in entries)

    def test_main_diff_unavailable_logs_status(
        self, monkeypatch, repo_after_merge: Path,
    ):
        """Force touched_paths to return None (e.g. subprocess fail post-Tier-2)
        → status 'diff_unavailable', no additionalContext, no phase-gates entry.
        """
        self._cd(monkeypatch, repo_after_merge)
        self._set_stdin(monkeypatch, make_bash("git merge feat/x"))
        monkeypatch.setattr(pa, "touched_paths", lambda _root: None)
        rc = pa.main()
        assert rc == 0
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        assert any(e.get("status") == "diff_unavailable" for e in entries)
        # phase-gates gets entries from the real merge setup is NOT pre-existing
        # in this fixture; assert no post_merge entry was added by our main() run.
        phase_path = repo_after_merge / ".claude" / "logs" / "phase-gates.jsonl"
        if phase_path.exists():
            phase = _read_jsonl(phase_path)
            # our main() run should not have appended a post_merge event
            assert all(e.get("event") != "post_merge" for e in phase)

    def test_main_merge_emits_additional_context_to_stdout(
        self, monkeypatch, repo_after_merge: Path, capsys,
    ):
        self._cd(monkeypatch, repo_after_merge)
        self._set_stdin(monkeypatch, make_bash("git merge feat/x"))
        rc = pa.main()
        assert rc == 0
        captured = capsys.readouterr().out.strip()
        payload = json.loads(captured)
        assert payload["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert "/pos:compound" in payload["hookSpecificOutput"]["additionalContext"]

    def test_main_pull_emits_additional_context(
        self, monkeypatch, repo_after_pull: Path, capsys,
    ):
        self._cd(monkeypatch, repo_after_pull)
        self._set_stdin(monkeypatch, make_bash("git pull origin main"))
        rc = pa.main()
        assert rc == 0
        captured = capsys.readouterr().out.strip()
        payload = json.loads(captured)
        assert "/pos:compound" in payload["hookSpecificOutput"]["additionalContext"]

    def test_main_gh_pr_merge_returns_zero_no_log(
        self, monkeypatch, repo_clean: Path,
    ):
        self._cd(monkeypatch, repo_clean)
        self._set_stdin(monkeypatch, make_bash("gh pr merge --squash"))
        rc = pa.main()
        assert rc == 0
        assert not (
            repo_clean / ".claude" / "logs" / "post-action.jsonl"
        ).exists()

    def test_main_docs_only_merge_confirmed_no_triggers(
        self, monkeypatch, repo_after_merge: Path,
    ):
        """Monkeypatch touched_paths to simulate a docs-only merge — exercises
        the 'confirmed_no_triggers' branch distinct from min_files_changed."""
        self._cd(monkeypatch, repo_after_merge)
        self._set_stdin(monkeypatch, make_bash("git merge feat/x"))
        monkeypatch.setattr(
            pa, "touched_paths",
            lambda _root: ["docs/A.md", "docs/B.md", "ROADMAP.md"],
        )
        rc = pa.main()
        assert rc == 0
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        assert any(e.get("status") == "confirmed_no_triggers" for e in entries)


# ---------------------------------------------------------------------------
# TestLogShape — stable log field contract
# ---------------------------------------------------------------------------


class TestLogShape:
    def test_confirmed_entry_contains_required_fields(
        self, repo_after_merge: Path,
    ):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        confirmed = next(
            e for e in entries
            if e.get("status") == "confirmed_triggers_matched"
        )
        assert "ts" in confirmed
        assert confirmed["hook"] == "post-action"
        assert "command" in confirmed
        assert "kind" in confirmed
        assert "touched_paths" in confirmed
        assert "triggers_matched" in confirmed

    def test_tier2_unconfirmed_entry_contains_kind_and_reflog(
        self, repo_clean: Path,
    ):
        run_hook(load_fixture("git_merge.json"), cwd=repo_clean)
        entries = _read_jsonl(
            repo_clean / ".claude" / "logs" / "post-action.jsonl"
        )
        skip = next(e for e in entries if e.get("status") == "tier2_unconfirmed")
        assert skip["hook"] == "post-action"
        assert skip["kind"] == "git_merge"
        assert "reflog" in skip  # reflog message that failed confirmation

    def test_phase_gates_entry_is_minimal(self, repo_after_merge: Path):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        phase = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "phase-gates.jsonl"
        )
        last = phase[-1]
        assert last["event"] == "post_merge"
        assert "ts" in last


# ---------------------------------------------------------------------------
# TestIdempotence — two runs same effect (append-only log is fine)
# ---------------------------------------------------------------------------


class TestIdempotence:
    def test_two_runs_append_two_entries(self, repo_after_merge: Path):
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        entries = _read_jsonl(
            repo_after_merge / ".claude" / "logs" / "post-action.jsonl"
        )
        confirmed = [
            e for e in entries
            if e.get("status") == "confirmed_triggers_matched"
        ]
        assert len(confirmed) == 2

    def test_two_runs_both_emit_additional_context(self, repo_after_merge: Path):
        r1 = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        r2 = run_hook(load_fixture("git_merge.json"), cwd=repo_after_merge)
        assert r1.returncode == 0
        assert r2.returncode == 0
        ctx1 = parse_stdout(r1)["hookSpecificOutput"]["additionalContext"]
        ctx2 = parse_stdout(r2)["hookSpecificOutput"]["additionalContext"]
        assert "/pos:compound" in ctx1
        assert "/pos:compound" in ctx2
