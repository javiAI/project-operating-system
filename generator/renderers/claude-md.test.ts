import { describe, expect, it } from "vitest";
import { render } from "./claude-md.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/claude-md", () => {
  it.each(profiles)("emits a single CLAUDE.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    expect(out[0].path).toBe("CLAUDE.md");
  });

  it.each(profiles)(
    "includes Fase -1 and Fase N+7 rules for $slug",
    ({ profile }) => {
      const content = render(profile)[0].content;
      expect(content).toContain("Fase -1");
      expect(content).toContain("Fase N+7 Context gate");
    }
  );

  it.each(profiles)("references the stack and testing framework for $slug", ({ profile }) => {
    const content = render(profile)[0].content;
    const stack = profile.answers.stack as Record<string, unknown>;
    const testing = profile.answers.testing as Record<string, unknown>;
    expect(content).toContain(String(stack.language));
    expect(content).toContain(String(testing.unit_framework));
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    expect(render(profile)[0].content.endsWith("\n")).toBe(true);
  });

  it.each(profiles)(
    "exposes user-specific TODO placeholders for partial canonical profile $slug",
    ({ profile }) => {
      const content = render(profile)[0].content;
      expect(content).toContain("TODO(identity.name)");
      expect(content).toContain("TODO(identity.owner)");
      expect(content).toContain("TODO(identity.description)");
    }
  );
});
