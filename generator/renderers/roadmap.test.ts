import { describe, expect, it } from "vitest";
import { render } from "./roadmap.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/roadmap", () => {
  it.each(profiles)("emits a single ROADMAP.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("ROADMAP.md");
  });

  it.each(profiles)("includes the progress table header and branch status legend for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("| Fase | Descripción | Estado |");
    expect(file?.content).toContain("⏳");
    expect(file?.content).toContain("✅");
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });
});
