import { describe, expect, it } from "vitest";
import { render } from "./master-plan.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/master-plan", () => {
  it.each(profiles)("emits a single MASTER_PLAN.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("MASTER_PLAN.md");
  });

  it.each(profiles)("includes §1 conventions and §2.1 Fase -1 gate for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("§1. Convenciones");
    expect(file?.content).toContain("§2.1 Fase -1");
    expect(file?.content).toContain("Kickoff block");
  });

  it.each(profiles)("mentions the generated project name in the heading for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain(`MASTER_PLAN — ${(profile.answers.identity as Record<string, unknown>).name}`);
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });
});
