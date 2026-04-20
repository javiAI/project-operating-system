import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { formatReport, validateProfileFile } from "./validate-profile.ts";

const SCHEMA = "questionnaire/schema.yaml";
const CLI = "tools/validate-profile.ts";

function runCli(args: string[]): { code: number; stdout: string; stderr: string } {
  const result = spawnSync("npx", ["tsx", CLI, ...args], {
    encoding: "utf8",
    env: { ...process.env, NODE_NO_WARNINGS: "1" },
  });
  return {
    code: result.status ?? -1,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  };
}

describe("validateProfileFile (unit)", () => {
  it("returns exit 0 for a valid canonical profile", async () => {
    const result = await validateProfileFile(SCHEMA, "questionnaire/profiles/nextjs-app.yaml");
    expect(result.exitCode).toBe(0);
    expect(result.ok).toBe(true);
    expect(result.issues).toEqual([]);
  });

  it("returns exit 2 when the profile file is missing", async () => {
    const result = await validateProfileFile(SCHEMA, "does-not-exist.yaml");
    expect(result.exitCode).toBe(2);
    expect(result.ok).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it("returns exit 2 when the profile is not valid YAML", async () => {
    const dir = mkdtempSync(join(tmpdir(), "profile-"));
    const path = join(dir, "broken.yaml");
    writeFileSync(path, "version: '0.1.0'\nprofile:\n  name: x\n  description: y\nanswers:\n  foo: [unterminated");
    const result = await validateProfileFile(SCHEMA, path);
    expect(result.exitCode).toBe(2);
  });

  it("returns exit 1 and lists issues for an invalid profile", async () => {
    const result = await validateProfileFile(SCHEMA, "tools/__fixtures__/profiles/invalid/unknown-path.yaml");
    expect(result.exitCode).toBe(1);
    expect(result.issues.length).toBeGreaterThan(0);
    expect(result.issues[0]?.kind).toBe("answer-unknown-path");
  });

  it("formatReport renders OK for a valid profile", async () => {
    const result = await validateProfileFile(SCHEMA, "questionnaire/profiles/cli-tool.yaml");
    const report = formatReport(result, SCHEMA, "questionnaire/profiles/cli-tool.yaml");
    expect(report).toMatch(/status: OK/);
  });

  it("formatReport renders FAIL with each issue line", async () => {
    const result = await validateProfileFile(SCHEMA, "tools/__fixtures__/profiles/invalid/enum-out-of-values.yaml");
    const report = formatReport(result, SCHEMA, "enum-out-of-values.yaml");
    expect(report).toMatch(/status: FAIL/);
    expect(report).toMatch(/answer-value-not-in-enum/);
  });
});

describe("validate-profile CLI (integration)", () => {
  it.each([
    "questionnaire/profiles/nextjs-app.yaml",
    "questionnaire/profiles/agent-sdk.yaml",
    "questionnaire/profiles/cli-tool.yaml",
  ])("exits 0 for canonical profile %s", (path) => {
    const r = runCli([path]);
    expect(r.code).toBe(0);
    expect(r.stdout).toMatch(/status: OK/);
  }, 30000);

  it("exits 1 and prints the issue kind for unknown-path fixture", () => {
    const r = runCli(["tools/__fixtures__/profiles/invalid/unknown-path.yaml"]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-unknown-path/);
  }, 30000);

  it("exits 1 for type-mismatch fixture", () => {
    const r = runCli(["tools/__fixtures__/profiles/invalid/type-mismatch.yaml"]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-type-mismatch/);
  }, 30000);

  it("exits 1 for enum-out-of-values fixture", () => {
    const r = runCli(["tools/__fixtures__/profiles/invalid/enum-out-of-values.yaml"]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-value-not-in-enum/);
  }, 30000);

  it("exits 1 for pattern-violation fixture", () => {
    const r = runCli(["tools/__fixtures__/profiles/invalid/pattern-violation.yaml"]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-constraint-violation/);
  }, 30000);

  it("exits 1 for array-item-type-mismatch fixture", () => {
    const r = runCli(["tools/__fixtures__/profiles/invalid/array-item-type-mismatch.yaml"]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-array-item-type-mismatch/);
  }, 30000);

  it("exits 2 when the profile file does not exist", () => {
    const r = runCli(["does-not-exist.yaml"]);
    expect(r.code).toBe(2);
  }, 30000);

  it("exits 2 when no profile path is given", () => {
    const r = runCli([]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/profile/i);
  }, 30000);
});
