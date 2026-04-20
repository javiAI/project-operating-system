import { describe, expect, it } from "vitest";
import { buildProfile, USER_SPECIFIC_PATHS, type Profile } from "./profile-model.ts";
import type { ProfileFile } from "./schema.ts";

function baseInput(answers: Record<string, unknown>): ProfileFile {
  return {
    version: "1.0.0",
    profile: { name: "nextjs-app", description: "canonical next.js profile" },
    answers,
  };
}

describe("buildProfile — meta", () => {
  it("copies version, profile.name and profile.description into meta", () => {
    const out = buildProfile(baseInput({}));
    expect(out.meta).toEqual({
      version: "1.0.0",
      profileName: "nextjs-app",
      profileDescription: "canonical next.js profile",
    });
  });
});

describe("buildProfile — dotted to nested", () => {
  it("converts a single top-level dotted key", () => {
    const out = buildProfile(baseInput({ "stack.language": "typescript" }));
    expect((out.answers.stack as Record<string, unknown>).language).toBe("typescript");
  });

  it("merges multiple keys under the same prefix", () => {
    const out = buildProfile(
      baseInput({ "stack.language": "typescript", "stack.runtime": "node" })
    );
    expect(out.answers.stack).toEqual({ language: "typescript", runtime: "node" });
  });

  it("supports 3+ levels of nesting", () => {
    const out = buildProfile(baseInput({ "stack.testing.framework": "vitest" }));
    expect(
      ((out.answers.stack as Record<string, unknown>).testing as Record<string, unknown>).framework
    ).toBe("vitest");
  });

  it("preserves value types (array, number, boolean, object)", () => {
    const out = buildProfile(
      baseInput({
        "stack.ci.providers": ["github", "gitlab"],
        "stack.ci.parallelism": 4,
        "stack.ci.cache": true,
        "stack.ci.matrix": { os: ["ubuntu", "macos"] },
      })
    );
    const ci = (out.answers.stack as Record<string, unknown>).ci as Record<string, unknown>;
    expect(ci.providers).toEqual(["github", "gitlab"]);
    expect(ci.parallelism).toBe(4);
    expect(ci.cache).toBe(true);
    expect(ci.matrix).toEqual({ os: ["ubuntu", "macos"] });
  });

  it("throws when a dotted key collides with an existing leaf prefix", () => {
    expect(() =>
      buildProfile(baseInput({ "stack": "typescript", "stack.language": "ts" }))
    ).toThrow(/collision/i);
  });

  it("throws when a dotted key would overwrite a nested object with a leaf", () => {
    expect(() =>
      buildProfile(baseInput({ "stack.language": "ts", "stack": "typescript" }))
    ).toThrow(/collision/i);
  });
});

describe("buildProfile — user-specific placeholders", () => {
  it("injects all 3 TODO placeholders when identity.* is absent", () => {
    const out = buildProfile(baseInput({}));
    const identity = out.answers.identity as Record<string, unknown>;
    expect(identity).toEqual({
      name: "TODO(identity.name)",
      description: "TODO(identity.description)",
      owner: "TODO(identity.owner)",
    });
    expect(out.placeholders).toEqual([
      "identity.name",
      "identity.description",
      "identity.owner",
    ]);
  });

  it("emits no placeholders when all user-specific fields are present", () => {
    const out = buildProfile(
      baseInput({
        "identity.name": "my-project",
        "identity.description": "my project",
        "identity.owner": "alice",
      })
    );
    const identity = out.answers.identity as Record<string, unknown>;
    expect(identity).toEqual({
      name: "my-project",
      description: "my project",
      owner: "alice",
    });
    expect(out.placeholders).toEqual([]);
  });

  it("injects only the missing user-specific field when others are present", () => {
    const out = buildProfile(
      baseInput({
        "identity.name": "my-project",
        "identity.owner": "alice",
      })
    );
    const identity = out.answers.identity as Record<string, unknown>;
    expect(identity.name).toBe("my-project");
    expect(identity.description).toBe("TODO(identity.description)");
    expect(identity.owner).toBe("alice");
    expect(out.placeholders).toEqual(["identity.description"]);
  });

  it("returns placeholders in USER_SPECIFIC_PATHS order (deterministic)", () => {
    const out = buildProfile(baseInput({ "identity.description": "desc" }));
    expect(out.placeholders).toEqual(["identity.name", "identity.owner"]);
  });

  it("exposes USER_SPECIFIC_PATHS as the canonical list", () => {
    expect(USER_SPECIFIC_PATHS).toEqual([
      "identity.name",
      "identity.description",
      "identity.owner",
    ]);
  });

  it("does not treat a non-user-specific missing field as a placeholder", () => {
    const out = buildProfile(baseInput({ "identity.name": "x", "identity.description": "y", "identity.owner": "z" }));
    expect(out.placeholders).toEqual([]);
    expect((out.answers.stack as unknown) ?? null).toBeNull();
  });
});

describe("buildProfile — determinism", () => {
  it("produces byte-equal JSON for the same input called twice", () => {
    const input = baseInput({
      "stack.language": "typescript",
      "stack.runtime": "node",
      "identity.name": "x",
    });
    const a: Profile = buildProfile(input);
    const b: Profile = buildProfile(input);
    expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
  });
});
