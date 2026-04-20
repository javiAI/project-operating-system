import { describe, expect, it } from "vitest";
import { render } from "./readme.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/readme", () => {
  it.each(profiles)("emits a single README.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("README.md");
  });

  it.each(profiles)("links to the 5 governance docs for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("(CLAUDE.md)");
    expect(file?.content).toContain("(AGENTS.md)");
    expect(file?.content).toContain("(HANDOFF.md)");
    expect(file?.content).toContain("(MASTER_PLAN.md)");
    expect(file?.content).toContain("(ROADMAP.md)");
  });

  it.each(profiles)("references the project description for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("TODO(identity.description)");
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });
});
