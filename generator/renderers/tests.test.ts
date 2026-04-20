import { describe, expect, it } from "vitest";
import { render } from "./tests.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";
import { buildProfile, type Profile } from "../lib/profile-model.ts";

const profiles = loadCanonicalProfiles();
const bySlug = Object.fromEntries(
  profiles.map((p) => [p.slug, p.profile])
) as Record<string, Profile>;

describe("renderers/tests — paths emitted per canonical profile", () => {
  it.each([
    [
      "nextjs-app",
      ["Makefile", "tests/README.md", "tests/smoke.test.ts", "vitest.config.ts"],
    ],
    [
      "cli-tool",
      ["Makefile", "tests/README.md", "tests/smoke.test.ts", "vitest.config.ts"],
    ],
    [
      "agent-sdk",
      ["Makefile", "pytest.ini", "tests/README.md", "tests/test_smoke.py"],
    ],
  ] as const)("%s emits the expected sorted paths", (slug, expected) => {
    const files = render(bySlug[slug]!);
    expect(files.map((f) => f.path).sort()).toEqual([...expected]);
  });
});

describe("renderers/tests — critical strings per stack", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "TS profile %s — smoke test has describe/expect, vitest.config has defineConfig",
    (slug) => {
      const files = render(bySlug[slug]!);
      const smoke = files.find((f) => f.path === "tests/smoke.test.ts");
      expect(smoke).toBeDefined();
      expect(smoke!.content).toMatch(/describe\s*\(/);
      expect(smoke!.content).toMatch(/expect\s*\(/);
      const config = files.find((f) => f.path === "vitest.config.ts");
      expect(config).toBeDefined();
      expect(config!.content).toMatch(/defineConfig/);
    }
  );

  it("python profile agent-sdk — smoke has def test_ + assert, pytest.ini has [pytest] + --cov", () => {
    const files = render(bySlug["agent-sdk"]!);
    const smoke = files.find((f) => f.path === "tests/test_smoke.py");
    expect(smoke).toBeDefined();
    expect(smoke!.content).toMatch(/def test_/);
    expect(smoke!.content).toMatch(/assert\s+/);
    const config = files.find((f) => f.path === "pytest.ini");
    expect(config).toBeDefined();
    expect(config!.content).toMatch(/\[pytest\]/);
    expect(config!.content).toMatch(/--cov/);
  });

  it.each(["nextjs-app", "cli-tool", "agent-sdk"])(
    "%s — Makefile has a 'test' target",
    (slug) => {
      const files = render(bySlug[slug]!);
      const mk = files.find((f) => f.path === "Makefile");
      expect(mk).toBeDefined();
      expect(mk!.content).toMatch(/^test:/m);
    }
  );
});

describe("renderers/tests — stack conditionals do not leak the other stack's framework", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "TS profile %s — no emitted file mentions pytest",
    (slug) => {
      const files = render(bySlug[slug]!);
      for (const f of files) {
        expect(f.content).not.toMatch(/\bpytest\b/i);
      }
    }
  );

  it("python profile agent-sdk — no emitted file mentions vitest", () => {
    const files = render(bySlug["agent-sdk"]!);
    for (const f of files) {
      expect(f.content).not.toMatch(/\bvitest\b/i);
    }
  });
});

describe("renderers/tests — coverage threshold reflected in config", () => {
  it.each(["nextjs-app", "cli-tool"])(
    "TS profile %s reflects coverage threshold in vitest.config.ts",
    (slug) => {
      const profile = bySlug[slug]!;
      const threshold = (profile.answers.testing as Record<string, unknown>)
        .coverage_threshold as number;
      const files = render(profile);
      const config = files.find((f) => f.path === "vitest.config.ts")!;
      expect(config.content).toContain(String(threshold));
    }
  );

  it("python profile agent-sdk reflects coverage threshold as --cov-fail-under=N in pytest.ini", () => {
    const profile = bySlug["agent-sdk"]!;
    const threshold = (profile.answers.testing as Record<string, unknown>)
      .coverage_threshold as number;
    const files = render(profile);
    const config = files.find((f) => f.path === "pytest.ini")!;
    expect(config.content).toMatch(
      new RegExp(`--cov-fail-under=${threshold}\\b`)
    );
  });
});

describe("renderers/tests — e2e framework reflected only in README (no config emitted)", () => {
  it("nextjs-app README mentions playwright but no playwright.config.ts file is emitted", () => {
    const files = render(bySlug["nextjs-app"]!);
    const readme = files.find((f) => f.path === "tests/README.md")!;
    expect(readme.content.toLowerCase()).toMatch(/playwright/);
    expect(files.map((f) => f.path)).not.toContain("playwright.config.ts");
  });

  it.each(["cli-tool", "agent-sdk"])(
    "%s README does not mention e2e tools when e2e_framework=none",
    (slug) => {
      const files = render(bySlug[slug]!);
      const readme = files.find((f) => f.path === "tests/README.md")!;
      expect(readme.content.toLowerCase()).not.toMatch(/playwright/);
      expect(readme.content.toLowerCase()).not.toMatch(/cypress/);
    }
  );

  it("python profile with e2e_framework!=none — README does NOT render the E2E section (Makefile has no test-e2e target in Python)", () => {
    const pythonWithE2e = buildProfile({
      version: "0.1.0",
      profile: { name: "py-e2e-fixture", description: "python + e2e synthetic fixture" },
      answers: {
        "domain.type": "cli",
        "stack.language": "python",
        "stack.database": "none",
        "testing.unit_framework": "pytest",
        "testing.coverage_threshold": 80,
        "testing.e2e_framework": "playwright",
        "workflow.ci_host": "github",
        "workflow.release_strategy": "manual",
        "workflow.branch_protection": true,
        "claude_code.default_model": "claude-sonnet-4-6",
      },
    });
    const files = render(pythonWithE2e);
    const readme = files.find((f) => f.path === "tests/README.md")!;
    expect(readme.content).not.toMatch(/## E2E —/);
    expect(readme.content).not.toMatch(/make test-e2e/);
    const mk = files.find((f) => f.path === "Makefile")!;
    expect(mk.content).not.toMatch(/^test-e2e:/m);
  });
});

describe("renderers/tests — every FileWrite ends with a trailing newline", () => {
  it.each(profiles)("$slug — every emitted file ends with \\n", ({ profile }) => {
    const files = render(profile);
    for (const f of files) {
      expect(f.content.endsWith("\n")).toBe(true);
    }
  });
});

describe("renderers/tests — deterministic across runs", () => {
  it.each(profiles)(
    "$slug — byte-identical FileWrite[] across runs",
    ({ profile }) => {
      expect(JSON.stringify(render(profile))).toBe(
        JSON.stringify(render(profile))
      );
    }
  );
});

describe("renderers/tests — deferred frameworks throw with descriptive messages", () => {
  function makeProfile(framework: string, language: string): Profile {
    return buildProfile({
      version: "0.1.0",
      profile: {
        name: "deferred-fixture",
        description: "deferred framework fixture",
      },
      answers: {
        "domain.type": "cli",
        "stack.language": language,
        "stack.database": "none",
        "testing.unit_framework": framework,
        "testing.coverage_threshold": 80,
        "testing.e2e_framework": "none",
        "workflow.ci_host": "github",
        "workflow.release_strategy": "manual",
        "workflow.branch_protection": true,
        "claude_code.default_model": "claude-sonnet-4-6",
      },
    });
  }

  it("jest (typescript) — throw mentions jest, 'deferred', and the field path", () => {
    const p = makeProfile("jest", "typescript");
    expect(() => render(p)).toThrow(/jest/);
    expect(() => render(p)).toThrow(/deferred/i);
    expect(() => render(p)).toThrow(/testing\.unit_framework/);
  });

  it("go-test (go) — throw mentions go-test, 'deferred', and the field path", () => {
    const p = makeProfile("go-test", "go");
    expect(() => render(p)).toThrow(/go-test/);
    expect(() => render(p)).toThrow(/deferred/i);
    expect(() => render(p)).toThrow(/testing\.unit_framework/);
  });

  it("cargo-test (rust) — throw mentions cargo-test, 'deferred', and the field path", () => {
    const p = makeProfile("cargo-test", "rust");
    expect(() => render(p)).toThrow(/cargo-test/);
    expect(() => render(p)).toThrow(/deferred/i);
    expect(() => render(p)).toThrow(/testing\.unit_framework/);
  });
});
