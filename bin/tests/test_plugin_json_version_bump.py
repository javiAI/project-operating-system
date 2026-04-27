"""F4 RED — pins .claude-plugin/plugin.json.version to F4 release.

Fails until plugin.json.version is bumped 0.0.1 -> 0.1.0.

Contract: plugin.json.version is the single source of truth for plugin
version. Git tag mirrors it as 'v' + version. Marketplace
plugins[0].source.ref must equal 'v' + version (covered by
test_marketplace_json_schema.py). Bumping version requires updating this
pin.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

EXPECTED_VERSION = "0.1.0"


class TestPluginVersionPin:
    def test_plugin_json_exists(self):
        assert PLUGIN_JSON.is_file(), f"missing: {PLUGIN_JSON}"

    def test_plugin_json_parses(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert isinstance(data, dict)

    def test_version_is_pinned_to_f4_release(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert data.get("version") == EXPECTED_VERSION, (
            f"plugin.json.version must be {EXPECTED_VERSION!r} (F4 first public release pin); "
            f"got {data.get('version')!r}"
        )
