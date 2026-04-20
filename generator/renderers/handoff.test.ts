import { describe, expect, it } from "vitest";
import { render } from "./handoff.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/handoff", () => {
  it.each(profiles)("emits a single HANDOFF.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    expect(out[0].path).toBe("HANDOFF.md");
  });

  it.each(profiles)(
    "includes the Fase N+7 Context gate matrix and checklist for $slug (carry-over)",
    ({ profile }) => {
      const content = render(profile)[0].content;
      expect(content).toContain("Fase N+7 Context gate");
      expect(content).toContain("`/clear`");
      expect(content).toContain("`/compact");
      expect(content).toContain("sesión nueva");
      expect(content).toContain("Claude nunca decide la opción por su cuenta");
    }
  );

  it.each(profiles)("includes the pre-flight checklist for $slug", ({ profile }) => {
    const content = render(profile)[0].content;
    expect(content).toContain("Pre-flight checklist");
    expect(content).toContain(".claude/branch-approvals/");
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    expect(render(profile)[0].content.endsWith("\n")).toBe(true);
  });
});
