import { describe, expect, it } from "vitest";
import { render } from "./claude-md.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/claude-md", () => {
  it.each(profiles)("emits a single CLAUDE.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("CLAUDE.md");
  });

  it.each(profiles)(
    "includes Fase -1 and Fase N+7 rules for $slug",
    ({ profile }) => {
      const [file] = render(profile);
      expect(file?.content).toContain("Fase -1");
      expect(file?.content).toContain("Fase N+7 Context gate");
    }
  );

  it.each(profiles)("references the stack and testing framework for $slug", ({ profile }) => {
    const [file] = render(profile);
    const stack = profile.answers.stack as Record<string, unknown>;
    const testing = profile.answers.testing as Record<string, unknown>;
    expect(file?.content).toContain(String(stack.language));
    expect(file?.content).toContain(String(testing.unit_framework));
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });

  it.each(profiles)(
    "exposes user-specific TODO placeholders for partial canonical profile $slug",
    ({ profile }) => {
      const [file] = render(profile);
      expect(file?.content).toContain("TODO(identity.name)");
      expect(file?.content).toContain("TODO(identity.owner)");
      expect(file?.content).toContain("TODO(identity.description)");
    }
  );
});
