import { describe, expect, it } from "vitest";
import { render } from "./rules.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/rules", () => {
  it.each(profiles)("emits exactly 2 files for $slug (C2 scope)", ({ profile }) => {
    expect(render(profile)).toHaveLength(2);
  });

  it.each(profiles)(
    "emits exact paths .claude/rules/docs.md and .claude/rules/patterns.md for $slug",
    ({ profile }) => {
      const paths = render(profile)
        .map((f) => f.path)
        .sort();
      expect(paths).toEqual([
        ".claude/rules/docs.md",
        ".claude/rules/patterns.md",
      ]);
    }
  );

  it.each(profiles)(
    "docs.md includes Fase N+7 traceability bullet for $slug",
    ({ profile }) => {
      const files = render(profile);
      const docs = files.find((f) => f.path === ".claude/rules/docs.md");
      expect(docs?.content).toContain("Trazabilidad de contexto");
      expect(docs?.content).toContain("HANDOFF.md");
    }
  );

  it.each(profiles)(
    "patterns.md includes pattern file format section for $slug",
    ({ profile }) => {
      const files = render(profile);
      const patterns = files.find(
        (f) => f.path === ".claude/rules/patterns.md"
      );
      expect(patterns?.content).toContain("Formato de un pattern file");
    }
  );

  it.each(profiles)(
    "all rule outputs end with a trailing newline for $slug",
    ({ profile }) => {
      for (const f of render(profile)) {
        expect(f.content.endsWith("\n")).toBe(true);
      }
    }
  );

  it.each(profiles)("is deterministic across runs for $slug", ({ profile }) => {
    expect(JSON.stringify(render(profile))).toBe(
      JSON.stringify(render(profile))
    );
  });
});
