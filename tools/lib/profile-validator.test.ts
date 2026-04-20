import { describe, expect, it } from "vitest";
import { parseProfileFile, validateProfile } from "./profile-validator.ts";
import { parseSchemaFile } from "./meta-schema.ts";

const baseSchema = parseSchemaFile({
  version: "0.1.0",
  sections: [
    {
      id: "A",
      name: "Identity",
      fields: [
        { path: "identity.name", type: "string", required: true, pattern: "^[a-z][a-z0-9-]{2,}$", minLength: 3, maxLength: 64 },
        { path: "identity.description", type: "string", minLength: 10, maxLength: 240 },
        { path: "identity.license", type: "enum", values: ["MIT", "Apache-2.0"], default: "MIT" },
      ],
    },
    {
      id: "C",
      name: "Stack",
      fields: [
        { path: "stack.language", type: "enum", values: ["typescript", "python"], required: true },
        { path: "stack.coverage", type: "number", default: 80, min: 0, max: 100 },
        { path: "stack.branch_protection", type: "boolean", default: true },
      ],
    },
    {
      id: "E",
      name: "Integrations",
      fields: [
        { path: "integrations.mcps", type: "array", items: "string", default: [], minItems: 0, maxItems: 5 },
        { path: "integrations.ports", type: "array", items: "number", default: [] },
      ],
    },
  ],
});

describe("parseProfileFile", () => {
  it("parses the canonical shape", () => {
    const parsed = parseProfileFile({
      version: "0.1.0",
      profile: { name: "nextjs-app", description: "Next.js 15 starter" },
      answers: { "stack.language": "typescript" },
    });
    expect(parsed.profile.name).toBe("nextjs-app");
    expect(parsed.answers["stack.language"]).toBe("typescript");
  });

  it("rejects missing version", () => {
    expect(() =>
      parseProfileFile({ profile: { name: "x", description: "y" }, answers: {} }),
    ).toThrow(/profile.*invalid/i);
  });

  it("rejects missing profile block", () => {
    expect(() => parseProfileFile({ version: "0.1.0", answers: {} })).toThrow(/profile/);
  });

  it("rejects extra top-level keys", () => {
    expect(() =>
      parseProfileFile({
        version: "0.1.0",
        profile: { name: "x", description: "desc" },
        answers: {},
        extra: true,
      }),
    ).toThrow(/unrecognized|extra/i);
  });
});

describe("validateProfile", () => {
  it("returns no issues for a valid partial profile", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.language": "typescript" },
    });
    expect(validateProfile(baseSchema, profile)).toEqual([]);
  });

  it("reports answer-unknown-path when the path is not in the schema", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.ghost": "x" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-unknown-path");
    expect(issues[0]?.path).toBe("stack.ghost");
  });

  it("reports answer-type-mismatch when a string field gets a number", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "identity.name": 42 },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-type-mismatch");
    expect(issues[0]?.path).toBe("identity.name");
  });

  it("reports answer-type-mismatch when a number field gets a string", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.coverage": "80" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-type-mismatch");
  });

  it("reports answer-type-mismatch when a boolean field gets a string", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.branch_protection": "true" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-type-mismatch");
  });

  it("reports answer-type-mismatch when an array field gets a scalar", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "integrations.mcps": "mempalace" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-type-mismatch");
  });

  it("reports answer-value-not-in-enum", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.language": "ruby" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-value-not-in-enum");
    expect(issues[0]?.detail).toMatch(/ruby/);
  });

  it("reports answer-value-not-in-enum for license enum", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "identity.license": "GPL-3.0" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-value-not-in-enum");
  });

  it("reports answer-array-item-type-mismatch when an item has wrong type", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "integrations.ports": [3000, "four-thousand"] },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-array-item-type-mismatch");
    expect(issues[0]?.path).toBe("integrations.ports");
  });

  it("reports answer-constraint-violation when pattern fails", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "identity.name": "INVALID_NAME" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-constraint-violation");
    expect(issues[0]?.detail).toMatch(/pattern/i);
  });

  it("reports answer-constraint-violation when minLength fails", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "identity.description": "too-short" },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-constraint-violation");
    expect(issues[0]?.detail).toMatch(/minLength/);
  });

  it("reports answer-constraint-violation when maxLength fails", () => {
    const longName = "a-" + "b".repeat(100);
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "identity.name": longName },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues.some((i) => i.kind === "answer-constraint-violation" && i.detail.includes("maxLength"))).toBe(true);
  });

  it("reports answer-constraint-violation when number is below min", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.coverage": -5 },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-constraint-violation");
    expect(issues[0]?.detail).toMatch(/min/);
  });

  it("reports answer-constraint-violation when number is above max", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "stack.coverage": 150 },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-constraint-violation");
    expect(issues[0]?.detail).toMatch(/max/);
  });

  it("reports answer-constraint-violation when array exceeds maxItems", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: { "integrations.mcps": ["a", "b", "c", "d", "e", "f"] },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("answer-constraint-violation");
    expect(issues[0]?.detail).toMatch(/maxItems/);
  });

  it("accepts a partial profile that omits required user-specific fields", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: {
        "stack.language": "typescript",
        "stack.coverage": 90,
      },
    });
    expect(validateProfile(baseSchema, profile)).toEqual([]);
  });

  it("collects multiple independent issues", () => {
    const profile = parseProfileFile({
      version: "0.1.0",
      profile: { name: "p", description: "desc" },
      answers: {
        "stack.language": "ruby",
        "stack.coverage": 999,
        "stack.ghost": true,
      },
    });
    const issues = validateProfile(baseSchema, profile);
    expect(issues).toHaveLength(3);
    const kinds = issues.map((i) => i.kind).sort();
    expect(kinds).toEqual(["answer-constraint-violation", "answer-unknown-path", "answer-value-not-in-enum"]);
  });
});
