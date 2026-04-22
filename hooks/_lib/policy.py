"""Declarative policy loader consumed by D3/D4/D5 hooks.

Parses `policy.yaml` at the repo root into typed dataclasses. Failure mode
(c.2): malformed / missing / wrong-shape policy.yaml → `None`. Callers
degrade to pass-through advisory; never propagates exception.

In-process cache keyed by policy path **only** (no mtime/size component —
no implicit invalidation on file edits). Hooks are ephemeral processes so
cache amortizes only within a single invocation; long-lived callers (tests,
future reuse) must call `reset_cache()` explicitly after editing the file.

See .claude/rules/hooks.md § Policy loader for consumer contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

POLICY_FILENAME = "policy.yaml"

_cache: dict[str, Any] | None = None
_cache_key: Path | None = None


@dataclass(frozen=True)
class ConditionalRule:
    if_touched: tuple[str, ...]
    then_required: tuple[str, ...]
    excludes: tuple[str, ...]


@dataclass(frozen=True)
class DocsSyncRules:
    baseline: tuple[str, ...]
    conditional: tuple[ConditionalRule, ...]


@dataclass(frozen=True)
class PostMergeTrigger:
    touched_paths_any_of: tuple[str, ...]
    skip_if_only: tuple[str, ...]
    min_files_changed: int


@dataclass(frozen=True)
class EnforcedPattern:
    label: str
    match_glob: str
    exclude_globs: tuple[str, ...]


@dataclass(frozen=True)
class PreWriteRules:
    enforced_patterns: tuple[EnforcedPattern, ...]


def _safe_str_list(val: Any) -> list[str] | None:
    """Return `val` as a `list[str]` if and only if every element is a string.

    Returns `None` if `val` is not a list, or if any element is not a string.
    The all-or-nothing shape preserves the loader's "wrong-shape → None"
    contract: silently dropping non-string entries would produce partial
    under-enforcement while still treating the policy as valid.
    """
    if not isinstance(val, list):
        return None
    if not all(isinstance(x, str) for x in val):
        return None
    return list(val)


def _optional_str_list(raw: Any, key_present: bool) -> list[str] | None:
    """List-shape validator for optional fields (e.g. `excludes`, `skip_if_only`).

    Distinguishes "missing key" from "present but wrong shape":
      - key absent (`key_present=False`)           → `[]` (sensible default)
      - key present, value is `list[str]`          → `list(val)`
      - key present, value is anything else        → `None` (signal wrong shape)

    Callers use the `None` signal to skip the rule/pattern or propagate it up
    to the accessor, keeping the "wrong-shape → None" contract strict for
    optional fields too. Previously `_safe_str_list(...) or []` coerced
    wrong-shape silently to empty, which could disable a declared exclusion.
    """
    if not key_present:
        return []
    return _safe_str_list(raw)


def _lifecycle_section(data: dict, section: str) -> dict | None:
    """Return `data["lifecycle"][section]` if the shape is well-formed, else None.

    Strict guard for the three accessors: a string/list in place of a
    mapping anywhere along the path must propagate as "wrong-shape → None",
    not an unhandled AttributeError that would escape the loader.

    A missing key (absent or `None`) at either level is treated as "section
    not declared" and returns an empty dict — caller decides whether that
    maps to a legitimate empty section or to `None` for its own contract.
    """
    lifecycle = data.get("lifecycle")
    if lifecycle is None:
        return {}
    if not isinstance(lifecycle, dict):
        return None
    section_val = lifecycle.get(section)
    if section_val is None:
        return {}
    if not isinstance(section_val, dict):
        return None
    return section_val


def _load_yaml(policy_path: Path) -> dict | None:
    if yaml is None:
        return None
    if not policy_path.exists():
        return None
    try:
        with policy_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def load_policy(repo_root: Path) -> dict | None:
    """Return the parsed policy dict for `repo_root/policy.yaml`, or None.

    Caches the parsed result keyed by absolute path only — edits to the
    file are NOT picked up until `reset_cache()` is called or the process
    restarts. Tests (and any long-lived caller) that mutate policy.yaml
    must call `reset_cache()` between reads.
    """
    global _cache, _cache_key
    policy_path = repo_root / POLICY_FILENAME
    if _cache_key == policy_path and _cache is not None:
        return _cache
    data = _load_yaml(policy_path)
    _cache = data
    _cache_key = policy_path
    return data


def reset_cache() -> None:
    """Clear the in-process cache. Primarily for test isolation."""
    global _cache, _cache_key
    _cache = None
    _cache_key = None


def docs_sync_rules(repo_root: Path) -> DocsSyncRules | None:
    data = load_policy(repo_root)
    if data is None:
        return None
    pr = _lifecycle_section(data, "pre_pr")
    if pr is None:
        return None
    baseline = _safe_str_list(pr.get("docs_sync_required"))
    cond_raw = pr.get("docs_sync_conditional")
    if baseline is None or not isinstance(cond_raw, list):
        return None
    conditional: list[ConditionalRule] = []
    for rule in cond_raw:
        if not isinstance(rule, dict):
            continue
        if_touched = _safe_str_list(rule.get("if_touched")) or []
        then_required = _safe_str_list(rule.get("then_required")) or []
        excludes = _optional_str_list(rule.get("excludes"), "excludes" in rule)
        if excludes is None:
            continue
        if not if_touched or not then_required:
            continue
        conditional.append(
            ConditionalRule(
                tuple(if_touched),
                tuple(then_required),
                tuple(excludes),
            )
        )
    return DocsSyncRules(tuple(baseline), tuple(conditional))


def post_merge_trigger(repo_root: Path) -> PostMergeTrigger | None:
    data = load_policy(repo_root)
    if data is None:
        return None
    pm = _lifecycle_section(data, "post_merge")
    if pm is None:
        return None
    skills = pm.get("skills_conditional")
    if not isinstance(skills, list) or not skills:
        return None
    first = skills[0]
    if not isinstance(first, dict):
        return None
    trigger = first.get("trigger")
    if not isinstance(trigger, dict):
        return None
    any_of = _safe_str_list(trigger.get("touched_paths_any_of"))
    skip_only = _optional_str_list(trigger.get("skip_if_only"), "skip_if_only" in trigger)
    min_files = trigger.get("min_files_changed")
    if (any_of is None or skip_only is None
            or not isinstance(min_files, int) or isinstance(min_files, bool)):
        return None
    return PostMergeTrigger(tuple(any_of), tuple(skip_only), min_files)


def pre_write_rules(repo_root: Path) -> PreWriteRules | None:
    data = load_policy(repo_root)
    if data is None:
        return None
    pw = _lifecycle_section(data, "pre_write")
    if pw is None:
        return None
    patterns_raw = pw.get("enforced_patterns")
    if not isinstance(patterns_raw, list):
        return None
    patterns: list[EnforcedPattern] = []
    for p in patterns_raw:
        if not isinstance(p, dict):
            continue
        label = p.get("label")
        match_glob = p.get("match_glob")
        exclude_globs = _optional_str_list(p.get("exclude_globs"), "exclude_globs" in p)
        if exclude_globs is None:
            continue
        if not isinstance(label, str) or not isinstance(match_glob, str):
            continue
        patterns.append(EnforcedPattern(label, match_glob, tuple(exclude_globs)))
    return PreWriteRules(tuple(patterns))


def derive_test_pair(rel_path: str, label: str) -> str | None:
    """Map an enforced file path to its expected test-pair location.

    Label-keyed derivation: Fase -1 decision (b.1) keeps derivation in code
    rather than inventing a YAML templating DSL. Consumers ask the loader
    "what is the expected test pair for this file under label X?" — the
    label comes from `pre_write_rules().enforced_patterns[*].label`.
    """
    if label == "hooks_top_level_py":
        if rel_path.startswith("hooks/") and rel_path.endswith(".py"):
            stem = rel_path[len("hooks/") : -len(".py")]
            if "/" in stem:
                return None
            return f"hooks/tests/test_{stem.replace('-', '_')}.py"
        return None
    if label == "generator_ts":
        if rel_path.endswith(".ts") and not rel_path.endswith(".test.ts"):
            return rel_path[: -len(".ts")] + ".test.ts"
        return None
    return None
