import { describe, expect, it } from "vitest";
import { parse as parseYaml } from "yaml";
import { render } from "./policy.ts";
import { loadCanonicalProfiles } from "../__tests__/load-canonical-profiles.ts";

const profiles = loadCanonicalProfiles();

describe("renderers/policy", () => {
  it.each(profiles)("emits a single policy.yaml for $slug", ({ profile }) => {
    const out = render(profile);
    expect(out).toHaveLength(1);
    expect(out[0]?.path).toBe("policy.yaml");
  });

  it.each(profiles)("emits valid YAML for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(() => parseYaml(file!.content)).not.toThrow();
  });

  it.each(profiles)("sets type to generated-project for $slug", ({ profile }) => {
    const [file] = render(profile);
    const parsed = parseYaml(file!.content) as Record<string, unknown>;
    expect(parsed.type).toBe("generated-project");
  });

  it.each(profiles)(
    "declares top-level keys version/project/token_budget/lifecycle/testing for $slug",
    ({ profile }) => {
      const [file] = render(profile);
      const parsed = parseYaml(file!.content) as Record<string, unknown>;
      expect(parsed.version).toBeDefined();
      expect(parsed.project).toBeDefined();
      expect(parsed.token_budget).toBeDefined();
      expect(parsed.lifecycle).toBeDefined();
      expect(parsed.testing).toBeDefined();
    }
  );

  it.each(profiles)(
    "uses TODO(identity.name) placeholder for project when canonical profile omits identity for $slug",
    ({ profile }) => {
      const [file] = render(profile);
      const parsed = parseYaml(file!.content) as Record<string, unknown>;
      expect(parsed.project).toBe("TODO(identity.name)");
    }
  );

  it("emits node framework without python framework for TS profiles (nextjs-app)", () => {
    const entry = profiles.find((p) => p.slug === "nextjs-app");
    const [file] = render(entry!.profile);
    const content = file!.content;
    const parsed = parseYaml(content) as Record<string, unknown>;
    const testing = parsed.testing as Record<string, unknown>;
    const unit = testing.unit as Record<string, unknown>;
    expect(unit.framework_node).toBe("vitest");
    expect(unit.framework_python).toBeUndefined();
    expect(content).not.toMatch(/\bpytest\b/);
  });

  it("emits node framework without python framework for TS profiles (cli-tool)", () => {
    const entry = profiles.find((p) => p.slug === "cli-tool");
    const [file] = render(entry!.profile);
    const content = file!.content;
    const parsed = parseYaml(content) as Record<string, unknown>;
    const testing = parsed.testing as Record<string, unknown>;
    const unit = testing.unit as Record<string, unknown>;
    expect(unit.framework_node).toBe("vitest");
    expect(unit.framework_python).toBeUndefined();
    expect(content).not.toMatch(/\bpytest\b/);
  });

  it("emits python framework without node framework for Python profiles (agent-sdk)", () => {
    const entry = profiles.find((p) => p.slug === "agent-sdk");
    const [file] = render(entry!.profile);
    const content = file!.content;
    const parsed = parseYaml(content) as Record<string, unknown>;
    const testing = parsed.testing as Record<string, unknown>;
    const unit = testing.unit as Record<string, unknown>;
    expect(unit.framework_python).toBe("pytest");
    expect(unit.framework_node).toBeUndefined();
    expect(content).not.toMatch(/\bvitest\b/);
  });

  it.each(profiles)("ends output with a trailing newline for $slug", ({ profile }) => {
    const [file] = render(profile);
    expect(file!.content.endsWith("\n")).toBe(true);
  });

  it.each(profiles)("is deterministic across runs for $slug", ({ profile }) => {
    expect(JSON.stringify(render(profile))).toBe(JSON.stringify(render(profile)));
  });
});
