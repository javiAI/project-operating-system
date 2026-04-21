import { describe, expect, it } from "vitest";
import { render } from "./skills-hooks-skeleton.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/skills-hooks-skeleton — paths emitted per canonical profile", () => {
  it.each(profiles)(
    "$slug — emits .claude/settings.json + .claude/hooks/README.md + .claude/skills/README.md",
    ({ profile }) => {
      const files = render(profile);
      expect(files.map((f) => f.path).sort()).toEqual([
        ".claude/hooks/README.md",
        ".claude/settings.json",
        ".claude/skills/README.md",
      ]);
    }
  );

  it.each(profiles)("$slug — emits exactly 3 files", ({ profile }) => {
    const files = render(profile);
    expect(files).toHaveLength(3);
  });
});

describe("renderers/skills-hooks-skeleton — settings.json structural invariants", () => {
  it.each(profiles)("$slug — .claude/settings.json is parseable JSON", ({ profile }) => {
    const files = render(profile);
    const settings = files.find((f) => f.path === ".claude/settings.json")!;
    expect(() => JSON.parse(settings.content)).not.toThrow();
  });

  it.each(profiles)(
    "$slug — settings.json has hooks === {} (empty object, populated by pos in Fase D)",
    ({ profile }) => {
      const files = render(profile);
      const settings = files.find((f) => f.path === ".claude/settings.json")!;
      const parsed = JSON.parse(settings.content) as Record<string, unknown>;
      expect(parsed.hooks).toBeDefined();
      expect(parsed.hooks).toEqual({});
    }
  );

  it.each(profiles)(
    "$slug — settings.json carries a non-empty _note string explaining the deferral",
    ({ profile }) => {
      const files = render(profile);
      const settings = files.find((f) => f.path === ".claude/settings.json")!;
      const parsed = JSON.parse(settings.content) as Record<string, unknown>;
      expect(typeof parsed._note).toBe("string");
      expect((parsed._note as string).length).toBeGreaterThan(40);
      expect(parsed._note as string).toMatch(/pos/);
    }
  );

  it.each(profiles)(
    "$slug — settings.json does NOT seed a permissions baseline (user decision: min conservador)",
    ({ profile }) => {
      const files = render(profile);
      const settings = files.find((f) => f.path === ".claude/settings.json")!;
      const parsed = JSON.parse(settings.content) as Record<string, unknown>;
      expect(parsed.permissions).toBeUndefined();
    }
  );
});

describe("renderers/skills-hooks-skeleton — READMEs document the deferral", () => {
  it.each(profiles)(
    "$slug — .claude/hooks/README.md mentions 'pos' and 'Fase D'",
    ({ profile }) => {
      const files = render(profile);
      const readme = files.find((f) => f.path === ".claude/hooks/README.md")!;
      expect(readme.content).toMatch(/\bpos\b/);
      expect(readme.content).toMatch(/Fase\s*D/);
    }
  );

  it.each(profiles)(
    "$slug — .claude/skills/README.md mentions 'pos' and 'Fase E'",
    ({ profile }) => {
      const files = render(profile);
      const readme = files.find((f) => f.path === ".claude/skills/README.md")!;
      expect(readme.content).toMatch(/\bpos\b/);
      expect(readme.content).toMatch(/Fase\s*E/);
    }
  );

  it.each(profiles)(
    "$slug — both READMEs explicitly mark content as deferred (no copy in C5)",
    ({ profile }) => {
      const files = render(profile);
      const hooksReadme = files.find((f) => f.path === ".claude/hooks/README.md")!;
      const skillsReadme = files.find((f) => f.path === ".claude/skills/README.md")!;
      expect(hooksReadme.content).toMatch(/diferid/i);
      expect(skillsReadme.content).toMatch(/diferid/i);
    }
  );
});

describe("renderers/skills-hooks-skeleton — every FileWrite ends with a trailing newline", () => {
  it.each(profiles)("$slug — every emitted file ends with \\n", ({ profile }) => {
    const files = render(profile);
    for (const f of files) {
      expect(f.content.endsWith("\n")).toBe(true);
    }
  });
});

describe("renderers/skills-hooks-skeleton — stack-agnostic (no stack leaks in C5)", () => {
  it.each(profiles)(
    "$slug — emitted content does not mention vitest, pytest, npm, pip, or language-specific tooling",
    ({ profile }) => {
      const files = render(profile);
      for (const f of files) {
        expect(f.content).not.toMatch(/\bvitest\b/i);
        expect(f.content).not.toMatch(/\bpytest\b/i);
        expect(f.content).not.toMatch(/\bnpm\b/i);
        expect(f.content).not.toMatch(/\bpip\b/i);
      }
    }
  );
});

describe("renderers/skills-hooks-skeleton — deterministic across runs", () => {
  it.each(profiles)(
    "$slug — byte-identical FileWrite[] across runs",
    ({ profile }) => {
      expect(JSON.stringify(render(profile))).toBe(
        JSON.stringify(render(profile))
      );
    }
  );
});
