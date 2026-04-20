import { describe, expect, it } from "vitest";
import {
  allRenderers,
  coreDocRenderers,
  policyAndRulesRenderers,
  testsHarnessRenderers,
} from "./index.ts";
import { renderAll } from "../lib/render-pipeline.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/index — coreDocRenderers", () => {
  it("exposes exactly 6 renderers (C1 scope)", () => {
    expect(coreDocRenderers).toHaveLength(6);
  });

  it("is frozen to prevent accidental mutation", () => {
    expect(Object.isFrozen(coreDocRenderers)).toBe(true);
  });

  it.each(profiles)(
    "produces the 6 expected file paths through the pipeline for $slug without collisions",
    ({ profile }) => {
      const files = renderAll(profile, [...coreDocRenderers]);
      expect(files.map((f) => f.path).sort()).toEqual([
        "AGENTS.md",
        "CLAUDE.md",
        "HANDOFF.md",
        "MASTER_PLAN.md",
        "README.md",
        "ROADMAP.md",
      ]);
    }
  );

  it.each(profiles)(
    "is deterministic: same profile yields byte-identical FileWrite[] across runs for $slug",
    ({ profile }) => {
      const a = renderAll(profile, [...coreDocRenderers]);
      const b = renderAll(profile, [...coreDocRenderers]);
      expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
    }
  );
});

describe("renderers/index — policyAndRulesRenderers (C2)", () => {
  it("exposes exactly 2 renderers (policy + rules, C2 scope)", () => {
    expect(policyAndRulesRenderers).toHaveLength(2);
  });

  it("is frozen to prevent accidental mutation", () => {
    expect(Object.isFrozen(policyAndRulesRenderers)).toBe(true);
  });
});

describe("renderers/index — testsHarnessRenderers (C3)", () => {
  it("exposes exactly 1 renderer (C3 scope)", () => {
    expect(testsHarnessRenderers).toHaveLength(1);
  });

  it("is frozen to prevent accidental mutation", () => {
    expect(Object.isFrozen(testsHarnessRenderers)).toBe(true);
  });
});

const ALL_RENDERERS_EXPECTED_PATHS: ReadonlyArray<readonly [string, readonly string[]]> = [
  [
    "nextjs-app",
    [
      ".claude/rules/docs.md",
      ".claude/rules/patterns.md",
      "AGENTS.md",
      "CLAUDE.md",
      "HANDOFF.md",
      "MASTER_PLAN.md",
      "Makefile",
      "README.md",
      "ROADMAP.md",
      "policy.yaml",
      "tests/README.md",
      "tests/smoke.test.ts",
      "vitest.config.ts",
    ],
  ],
  [
    "cli-tool",
    [
      ".claude/rules/docs.md",
      ".claude/rules/patterns.md",
      "AGENTS.md",
      "CLAUDE.md",
      "HANDOFF.md",
      "MASTER_PLAN.md",
      "Makefile",
      "README.md",
      "ROADMAP.md",
      "policy.yaml",
      "tests/README.md",
      "tests/smoke.test.ts",
      "vitest.config.ts",
    ],
  ],
  [
    "agent-sdk",
    [
      ".claude/rules/docs.md",
      ".claude/rules/patterns.md",
      "AGENTS.md",
      "CLAUDE.md",
      "HANDOFF.md",
      "MASTER_PLAN.md",
      "Makefile",
      "README.md",
      "ROADMAP.md",
      "policy.yaml",
      "pytest.ini",
      "tests/README.md",
      "tests/test_smoke.py",
    ],
  ],
];

describe("renderers/index — allRenderers (C3 composition)", () => {
  it("is frozen", () => {
    expect(Object.isFrozen(allRenderers)).toBe(true);
  });

  it.each(ALL_RENDERERS_EXPECTED_PATHS)(
    "produces the expected file paths through the pipeline for %s without collisions",
    (slug, expected) => {
      const profile = profiles.find((p) => p.slug === slug)!.profile;
      const files = renderAll(profile, [...allRenderers]);
      expect(files.map((f) => f.path).sort()).toEqual([...expected]);
    }
  );

  it.each(profiles)(
    "is deterministic: byte-identical FileWrite[] across runs for $slug",
    ({ profile }) => {
      const a = renderAll(profile, [...allRenderers]);
      const b = renderAll(profile, [...allRenderers]);
      expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
    }
  );
});
