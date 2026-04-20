import { describe, expect, it } from "vitest";
import { render } from "./agents.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/agents", () => {
  it.each(profiles)("emits a single AGENTS.md for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    const [file] = out;
    expect(file?.path).toBe("AGENTS.md");
  });

  it.each(profiles)(
    "includes Fase N+7 as last step of the branch flow for $slug (carry-over)",
    ({ profile }) => {
      const [file] = render(profile);
      expect(file?.content).toContain("Fase N+7 Context gate");
      expect(file?.content).toContain("puerta de entrada a la siguiente rama");
      expect(file?.content).toContain("Esperar elección explícita");
    }
  );

  it.each(profiles)('includes "continúa" autonomous flow for $slug', ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content).toContain("continúa");
    expect(file?.content).toContain("Fase -1");
  });

  it.each(profiles)("ends the output with a newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file?.content.endsWith("\n")).toBe(true);
  });
});
