"""F4 RED — locks down .github/workflows/release.yml contract.

Fails until:
- .github/workflows/release.yml exists and parses as YAML
- on.push.tags includes 'v*'
- jobs present: version-match, selftest, build-bundle, publish-release, mirror-marketplace
- publish-release.needs includes version-match, selftest, build-bundle
- mirror-marketplace is conditional/skippable (has 'if:' guard or env-gated step)
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"

EXPECTED_JOBS = {
    "version-match",
    "selftest",
    "build-bundle",
    "publish-release",
    "mirror-marketplace",
}

PUBLISH_RELEASE_REQUIRED_NEEDS = {"version-match", "selftest", "build-bundle"}


def _load_workflow():
    assert RELEASE_WORKFLOW.is_file(), f"missing: {RELEASE_WORKFLOW}"
    return yaml.safe_load(RELEASE_WORKFLOW.read_text())


class TestReleaseWorkflowShape:
    def test_release_yml_exists(self):
        assert RELEASE_WORKFLOW.is_file(), f"missing: {RELEASE_WORKFLOW}"

    def test_release_yml_parses(self):
        data = _load_workflow()
        assert isinstance(data, dict), "release.yml must parse to a YAML mapping"


class TestReleaseTrigger:
    def test_trigger_on_tag_v_star(self):
        data = _load_workflow()
        # PyYAML parses 'on:' as Python boolean True; accept either key.
        on_block = data.get("on") if "on" in data else data.get(True)
        assert on_block is not None, "workflow must declare 'on:' triggers"
        push = on_block.get("push") if isinstance(on_block, dict) else None
        assert push is not None, "workflow must trigger on push"
        tags = push.get("tags") if isinstance(push, dict) else None
        assert tags is not None, "workflow must trigger on push.tags"
        assert "v*" in tags, f"push.tags must include 'v*', got {tags!r}"


class TestReleaseJobs:
    def test_all_expected_jobs_present(self):
        data = _load_workflow()
        jobs = data.get("jobs", {})
        missing = EXPECTED_JOBS - set(jobs.keys())
        assert not missing, f"missing jobs: {sorted(missing)}; got {sorted(jobs.keys())}"

    def test_publish_release_depends_on_required_jobs(self):
        data = _load_workflow()
        publish = data.get("jobs", {}).get("publish-release", {})
        needs = publish.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        missing = PUBLISH_RELEASE_REQUIRED_NEEDS - set(needs)
        assert not missing, (
            f"publish-release.needs must include {sorted(PUBLISH_RELEASE_REQUIRED_NEEDS)}, "
            f"got {needs!r}; missing {sorted(missing)}"
        )

    def test_mirror_marketplace_is_conditional(self):
        data = _load_workflow()
        mirror = data.get("jobs", {}).get("mirror-marketplace", {})
        # Either job-level `if:` guard or every step gated by `if:` is acceptable;
        # a job-level guard is the simplest, most auditable form.
        job_if = mirror.get("if")
        steps = mirror.get("steps", [])
        any_step_if = any(isinstance(s, dict) and s.get("if") for s in steps)
        assert job_if or any_step_if, (
            "mirror-marketplace must be conditional/skippable (job-level 'if:' or step-level 'if:'); "
            "the public marketplace repo may not exist yet"
        )
