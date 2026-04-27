"""F4 RED — locks down .claude-plugin/marketplace.json contract.

Fails until:
- .claude-plugin/marketplace.json exists and parses as JSON
- Top-level keys present: name, owner, plugins
- owner.name present
- plugins[0].name matches plugin.json.name ("pos")
- plugins[0].source.source == "github"
- plugins[0].source.repo == "javiAI/project-operating-system"
- plugins[0].source.ref == "v" + plugin.json.version
- if plugins[0].version present, equals plugin.json.version
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


def _load_marketplace():
    assert MARKETPLACE_JSON.is_file(), f"missing: {MARKETPLACE_JSON}"
    return json.loads(MARKETPLACE_JSON.read_text())


def _load_plugin():
    assert PLUGIN_JSON.is_file(), f"missing: {PLUGIN_JSON}"
    return json.loads(PLUGIN_JSON.read_text())


class TestMarketplaceTopLevel:
    def test_marketplace_json_exists(self):
        assert MARKETPLACE_JSON.is_file(), f"missing: {MARKETPLACE_JSON}"

    def test_marketplace_json_parses(self):
        data = _load_marketplace()
        assert isinstance(data, dict), "marketplace.json must be a JSON object"

    def test_top_level_name_present(self):
        data = _load_marketplace()
        assert "name" in data, "top-level 'name' required"
        assert isinstance(data["name"], str) and data["name"].strip(), "'name' must be non-empty string"

    def test_top_level_owner_present(self):
        data = _load_marketplace()
        assert "owner" in data, "top-level 'owner' required"
        assert isinstance(data["owner"], dict), "'owner' must be an object"

    def test_top_level_plugins_present(self):
        data = _load_marketplace()
        assert "plugins" in data, "top-level 'plugins' required"
        assert isinstance(data["plugins"], list) and data["plugins"], "'plugins' must be non-empty list"


class TestMarketplaceOwner:
    def test_owner_name_present(self):
        data = _load_marketplace()
        assert "name" in data["owner"], "owner.name required"
        assert isinstance(data["owner"]["name"], str) and data["owner"]["name"].strip()


class TestMarketplacePluginEntry:
    def test_plugin_has_required_keys(self):
        data = _load_marketplace()
        plugin = data["plugins"][0]
        assert "name" in plugin, "plugins[0].name required"
        assert "source" in plugin, "plugins[0].source required"

    def test_plugin_name_matches_plugin_json(self):
        data = _load_marketplace()
        plugin_meta = _load_plugin()
        assert data["plugins"][0]["name"] == plugin_meta["name"], (
            f"marketplace plugin name {data['plugins'][0]['name']!r} != plugin.json name {plugin_meta['name']!r}"
        )

    def test_plugin_source_is_github(self):
        data = _load_marketplace()
        source = data["plugins"][0]["source"]
        assert isinstance(source, dict), "plugins[0].source must be an object"
        assert source.get("source") == "github", f"source.source must be 'github', got {source.get('source')!r}"

    def test_plugin_source_repo_pinned(self):
        data = _load_marketplace()
        source = data["plugins"][0]["source"]
        assert source.get("repo") == "javiAI/project-operating-system", (
            f"source.repo must be 'javiAI/project-operating-system', got {source.get('repo')!r}"
        )

    def test_plugin_source_ref_matches_plugin_version(self):
        data = _load_marketplace()
        plugin_meta = _load_plugin()
        source = data["plugins"][0]["source"]
        expected_ref = "v" + plugin_meta["version"]
        assert source.get("ref") == expected_ref, (
            f"source.ref must be {expected_ref!r}, got {source.get('ref')!r}"
        )

    def test_plugin_version_matches_plugin_json_when_present(self):
        data = _load_marketplace()
        plugin_meta = _load_plugin()
        plugin = data["plugins"][0]
        if "version" in plugin:
            assert plugin["version"] == plugin_meta["version"], (
                f"marketplace plugin version {plugin['version']!r} != plugin.json version {plugin_meta['version']!r}"
            )
