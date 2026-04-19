import { describe, expect, it } from "vitest";
import { validateQuestionnaire } from "../validate-questionnaire.ts";

describe("validate-questionnaire / integration", () => {
  it("returns exit 0 + ok=true on valid fixture", async () => {
    const result = await validateQuestionnaire(
      "tools/__fixtures__/valid/schema.yaml",
      "tools/__fixtures__/valid/questions.yaml"
    );
    expect(result.exitCode).toBe(0);
    expect(result.ok).toBe(true);
    expect(result.issues).toHaveLength(0);
  });

  it("returns exit 1 + issue when maps_to points to unknown path", async () => {
    const result = await validateQuestionnaire(
      "tools/__fixtures__/invalid-maps-to/schema.yaml",
      "tools/__fixtures__/invalid-maps-to/questions.yaml"
    );
    expect(result.exitCode).toBe(1);
    expect(result.ok).toBe(false);
    expect(result.issues.some((i) => i.kind === "maps_to-unknown-path")).toBe(true);
  });

  it("returns exit 2 on bad YAML syntax", async () => {
    const result = await validateQuestionnaire(
      "tools/__fixtures__/bad-yaml/schema.yaml",
      "tools/__fixtures__/bad-yaml/questions.yaml"
    );
    expect(result.exitCode).toBe(2);
    expect(result.ok).toBe(false);
    expect(result.errors.join("\n")).toMatch(/cannot parse/i);
  });

  it("returns exit 2 when schema file does not exist", async () => {
    const result = await validateQuestionnaire(
      "tools/__fixtures__/does-not-exist/schema.yaml",
      "tools/__fixtures__/valid/questions.yaml"
    );
    expect(result.exitCode).toBe(2);
  });
});
