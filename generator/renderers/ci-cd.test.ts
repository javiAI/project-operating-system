import { describe, expect, it } from "vitest";
import { parse as parseYaml } from "yaml";
import { render } from "./ci-cd.ts";
import { buildProfile, type Profile } from "../lib/profile-model.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();
const bySlug = Object.fromEntries(
  profiles.map((p) => [p.slug, p.profile])
) as Record<string, Profile>;

const SHA_PIN = /@[a-f0-9]{40}\b/;

function makeProfile(overrides: Record<string, unknown>): Profile {
  return buildProfile({
    version: "0.1.0",
    profile: { name: "synthetic-ci", description: "synthetic ci fixture" },
    answers: {
      "domain.type": "cli",
      "stack.language": "typescript",
      "stack.database": "none",
      "testing.unit_framework": "vitest",
      "testing.coverage_threshold": 80,
      "testing.e2e_framework": "none",
      "workflow.ci_host": "github",
      "workflow.release_strategy": "manual",
      "workflow.branch_protection": true,
      "claude_code.default_model": "claude-sonnet-4-6",
      ...overrides,
    },
  });
}

describe("renderers/ci-cd — paths emitted per canonical profile", () => {
  it.each([
    ["nextjs-app", [".github/workflows/ci.yml", "docs/BRANCH_PROTECTION.md"]],
    ["cli-tool", [".github/workflows/ci.yml", "docs/BRANCH_PROTECTION.md"]],
    ["agent-sdk", [".github/workflows/ci.yml", "docs/BRANCH_PROTECTION.md"]],
  ] as const)("%s emits the expected sorted paths", (slug, expected) => {
    const files = render(bySlug[slug]!);
    expect(files.map((f) => f.path).sort()).toEqual([...expected]);
  });
});

describe("renderers/ci-cd — workflow yaml structural invariants", () => {
  it.each(profiles)("$slug — ci.yml is parseable YAML", ({ profile }) => {
    const files = render(profile);
    const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
    expect(() => parseYaml(yml.content)).not.toThrow();
  });

  it.each(profiles)(
    "$slug — workflow has a stable top-level name: 'ci'",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      const parsed = parseYaml(yml.content) as Record<string, unknown>;
      expect(parsed.name).toBe("ci");
    }
  );

  it.each(profiles)(
    "$slug — workflow fires on pull_request to main and push to main",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      const parsed = parseYaml(yml.content) as Record<string, unknown>;
      const on = parsed.on as Record<string, { branches?: string[] }>;
      expect(on.pull_request?.branches).toEqual(["main"]);
      expect(on.push?.branches).toEqual(["main"]);
    }
  );

  it.each(profiles)(
    "$slug — every 'uses:' action is pinned by full SHA (40 hex chars)",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      const usesLines = yml.content
        .split("\n")
        .filter((l) => /^\s*-?\s*uses:\s+/.test(l));
      expect(usesLines.length).toBeGreaterThan(0);
      for (const line of usesLines) {
        expect(line).toMatch(SHA_PIN);
        expect(line).not.toMatch(/@v\d+$/);
      }
    }
  );
});

describe("renderers/ci-cd — stable job names by stack", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "%s (TS) — declares a single 'unit' job",
    (slug) => {
      const files = render(bySlug[slug]!);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      const parsed = parseYaml(yml.content) as Record<string, unknown>;
      const jobs = parsed.jobs as Record<string, unknown>;
      expect(Object.keys(jobs).sort()).toEqual(["unit"]);
    }
  );

  it("agent-sdk (Python) — declares a single 'unit' job", () => {
    const files = render(bySlug["agent-sdk"]!);
    const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
    const parsed = parseYaml(yml.content) as Record<string, unknown>;
    const jobs = parsed.jobs as Record<string, unknown>;
    expect(Object.keys(jobs).sort()).toEqual(["unit"]);
  });
});

describe("renderers/ci-cd — Makefile targets invoked (no direct binaries)", () => {
  it.each(profiles)(
    "$slug — workflow invokes 'make test-unit' explicitly",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      expect(yml.content).toMatch(/\bmake\s+test-unit\b/);
    }
  );

  it.each(profiles)(
    "$slug — workflow invokes 'make test-coverage' explicitly",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      expect(yml.content).toMatch(/\bmake\s+test-coverage\b/);
    }
  );

  it.each(profiles)(
    "$slug — workflow does NOT call vitest/pytest/npx binaries directly",
    ({ profile }) => {
      const files = render(profile);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      expect(yml.content).not.toMatch(/\bnpx\s+vitest\b/);
      expect(yml.content).not.toMatch(/\bpython3?\s+-m\s+pytest\b/);
      expect(yml.content).not.toMatch(/^\s*run:\s*pytest\b/m);
      expect(yml.content).not.toMatch(/^\s*run:\s*vitest\b/m);
    }
  );
});

describe("renderers/ci-cd — stack conditionals do not leak", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "%s (TS) — workflow mentions Node runtime and not Python setup",
    (slug) => {
      const files = render(bySlug[slug]!);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      expect(yml.content).toMatch(/setup-node/);
      expect(yml.content).toMatch(/node-version:\s*["']?20\.17\.0["']?/);
      expect(yml.content).not.toMatch(/setup-python/);
      expect(yml.content).not.toMatch(/pytest-cov/);
    }
  );

  it("agent-sdk (Python) — workflow mentions Python 3.11 and not Node setup", () => {
    const files = render(bySlug["agent-sdk"]!);
    const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
    expect(yml.content).toMatch(/setup-python/);
    expect(yml.content).toMatch(/python-version:\s*["']?3\.11["']?/);
    expect(yml.content).toMatch(/pytest-cov/);
    expect(yml.content).not.toMatch(/setup-node/);
    expect(yml.content).not.toMatch(/\bnpm\b/);
  });
});

describe("renderers/ci-cd — TS test deps install step (contract closure)", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "%s (TS) — workflow installs vitest + @vitest/coverage-v8 with pinned versions before invoking make",
    (slug) => {
      const files = render(bySlug[slug]!);
      const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
      expect(yml.content).toMatch(/name:\s*Install test deps/);
      expect(yml.content).toMatch(/npm\s+install\s+--no-save/);
      expect(yml.content).toMatch(/vitest@\d+\.\d+\.\d+/);
      expect(yml.content).toMatch(/@vitest\/coverage-v8@\d+\.\d+\.\d+/);

      const installIdx = yml.content.indexOf("Install test deps");
      const testUnitIdx = yml.content.indexOf("make test-unit");
      expect(installIdx).toBeGreaterThan(-1);
      expect(testUnitIdx).toBeGreaterThan(installIdx);
    }
  );

  it("agent-sdk (Python) — workflow does NOT declare a Node 'Install test deps' step (npm/vitest must not leak)", () => {
    const files = render(bySlug["agent-sdk"]!);
    const yml = files.find((f) => f.path === ".github/workflows/ci.yml")!;
    expect(yml.content).not.toMatch(/npm\s+install/);
    expect(yml.content).not.toMatch(/vitest/);
    expect(yml.content).not.toMatch(/@vitest\/coverage-v8/);
  });
});

describe("renderers/ci-cd — BRANCH_PROTECTION.md consistency with ci.yml", () => {
  it.each(profiles)(
    "$slug — BRANCH_PROTECTION.md lists the 'unit' job required check",
    ({ profile }) => {
      const files = render(profile);
      const doc = files.find((f) => f.path === "docs/BRANCH_PROTECTION.md")!;
      expect(doc.content).toMatch(/unit/);
    }
  );

  it.each(profiles)(
    "$slug — BRANCH_PROTECTION.md references 'main' as protected branch",
    ({ profile }) => {
      const files = render(profile);
      const doc = files.find((f) => f.path === "docs/BRANCH_PROTECTION.md")!;
      expect(doc.content).toMatch(/\bmain\b/);
    }
  );
});

describe("renderers/ci-cd — branch_protection=false omits BRANCH_PROTECTION.md", () => {
  it("emits only ci.yml when branch_protection=false", () => {
    const p = makeProfile({ "workflow.branch_protection": false });
    const files = render(p);
    expect(files.map((f) => f.path).sort()).toEqual([
      ".github/workflows/ci.yml",
    ]);
    expect(files.find((f) => f.path === "docs/BRANCH_PROTECTION.md")).toBeUndefined();
  });
});

describe("renderers/ci-cd — deferred ci_hosts throw with descriptive messages", () => {
  it.each(["gitlab", "bitbucket"])("%s — throws mentioning host, path, 'deferred'", (host) => {
    const p = makeProfile({ "workflow.ci_host": host });
    expect(() => render(p)).toThrow(new RegExp(host));
    expect(() => render(p)).toThrow(/deferred/i);
    expect(() => render(p)).toThrow(/workflow\.ci_host/);
  });
});

describe("renderers/ci-cd — every FileWrite ends with a trailing newline", () => {
  it.each(profiles)("$slug — every emitted file ends with \\n", ({ profile }) => {
    const files = render(profile);
    for (const f of files) {
      expect(f.content.endsWith("\n")).toBe(true);
    }
  });
});

describe("renderers/ci-cd — deterministic across runs", () => {
  it.each(profiles)(
    "$slug — byte-identical FileWrite[] across runs",
    ({ profile }) => {
      expect(JSON.stringify(render(profile))).toBe(
        JSON.stringify(render(profile))
      );
    }
  );
});
