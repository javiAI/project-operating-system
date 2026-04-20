import { describe, expect, it } from "vitest";
import { render } from "./handoff.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/handoff", () => {
  it.each(profiles)("emits a single HANDOFF.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("HANDOFF.md");
  });

  it.each(profiles)(
    "includes the Fase N+7 Context gate matrix and checklist for $slug (carry-over)",
    ({ profile }) => {
      const [file] = render(profile);
      expect(file?.content).toContain("Fase N+7 Context gate");
      expect(file?.content).toContain("`/clear`");
      expect(file?.content).toContain("`/compact");
      expect(file?.content).toContain("sesión nueva");
      expect(file?.content).toContain("Claude nunca decide la opción por su cuenta");
    }
  );

  it.each(profiles)("includes the pre-flight checklist for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("Pre-flight checklist");
    expect(file?.content).toContain(".claude/branch-approvals/");
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });
});
