import { describe, expect, it } from "vitest";
import {
  allRenderers,
  coreDocRenderers,
  policyAndRulesRenderers,
} from "./index.ts";
import { renderAll } from "../lib/render-pipeline.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

describe("renderers/index — coreDocRenderers", () => {
  it("exposes exactly 6 renderers (C1 scope)", () => {
    expect(coreDocRenderers).toHaveLength(6);
  });

  it("is frozen to prevent accidental mutation", () => {
    expect(Object.isFrozen(coreDocRenderers)).toBe(true);
  });

  const profiles = loadCanonicalProfiles();

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

describe("renderers/index — allRenderers (C2 composition)", () => {
  it("equals coreDocRenderers concatenated with policyAndRulesRenderers", () => {
    expect([...allRenderers]).toEqual([
      ...coreDocRenderers,
      ...policyAndRulesRenderers,
    ]);
  });

  it("is frozen", () => {
    expect(Object.isFrozen(allRenderers)).toBe(true);
  });

  const profiles = loadCanonicalProfiles();

  it.each(profiles)(
    "produces the 9 expected file paths through the pipeline for $slug without collisions",
    ({ profile }) => {
      const files = renderAll(profile, [...allRenderers]);
      expect(files.map((f) => f.path).sort()).toEqual([
        ".claude/rules/docs.md",
        ".claude/rules/patterns.md",
        "AGENTS.md",
        "CLAUDE.md",
        "HANDOFF.md",
        "MASTER_PLAN.md",
        "README.md",
        "ROADMAP.md",
        "policy.yaml",
      ]);
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
