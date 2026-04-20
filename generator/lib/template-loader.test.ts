import path from "node:path";
import { describe, expect, it } from "vitest";
import { loadTemplate, TEMPLATES_DIR } from "./template-loader.ts";

describe("loadTemplate", () => {
  it("resolves templates relative to the repo-level templates/ dir", () => {
    expect(path.basename(TEMPLATES_DIR)).toBe("templates");
  });

  it("loads and compiles an existing template", () => {
    const render = loadTemplate("CLAUDE.md.hbs");
    expect(typeof render).toBe("function");
  });

  it("exposes registered helpers to the compiled template", () => {
    const render = loadTemplate("CLAUDE.md.hbs");
    const output = render({
      meta: { version: "1.0.0", profileName: "p", profileDescription: "d" },
      answers: {
        identity: { name: "demo", description: "demo description", owner: "me" },
        domain: { type: "cli" },
        stack: { language: "typescript", database: "none" },
        testing: { unit_framework: "vitest", coverage_threshold: 90 },
      },
      placeholders: [],
    });
    expect(output).toContain("# CLAUDE.md — demo");
  });

  it("throws a descriptive error when the template does not exist", () => {
    expect(() => loadTemplate("does-not-exist.hbs")).toThrow(/ENOENT|no such file/i);
  });

  it("rejects an absolute path", () => {
    expect(() => loadTemplate("/etc/passwd")).toThrow(/absolute path rejected/);
  });

  it("rejects a path that escapes TEMPLATES_DIR via ../", () => {
    expect(() => loadTemplate("../package.json")).toThrow(/escapes templates dir/);
  });

  it("rejects a nested path that escapes TEMPLATES_DIR", () => {
    expect(() => loadTemplate("a/../../package.json")).toThrow(/escapes templates dir/);
  });
});
