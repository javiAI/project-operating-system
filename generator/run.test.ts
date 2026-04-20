import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { formatReport, runValidation } from "./run.ts";

const CLI = "generator/run.ts";

const VALID = "generator/__fixtures__/profiles/valid-partial/profile.yaml";
const MISSING_REQ = "generator/__fixtures__/profiles/missing-required/profile.yaml";
const INVALID_VAL = "generator/__fixtures__/profiles/invalid-value/profile.yaml";

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

describe("runValidation (unit)", () => {
  it("exit 0 with user-specific warnings for a valid-partial profile", async () => {
    const r = await runValidation(VALID);
    expect(r.exitCode).toBe(0);
    expect(r.ok).toBe(true);
    expect(r.issues).toEqual([]);
    expect(r.errors).toEqual([]);
    expect(r.warnings.map((w) => w.path).sort()).toEqual([
      "identity.description",
      "identity.name",
      "identity.owner",
    ]);
  });

  it("exit 1 when a non-user-specific required is missing", async () => {
    const r = await runValidation(MISSING_REQ);
    expect(r.exitCode).toBe(1);
    expect(r.ok).toBe(false);
    expect(r.errors.some((e) => e.path === "domain.type")).toBe(true);
  });

  it("exit 1 when a value is out of the enum (answer-value-not-in-enum)", async () => {
    const r = await runValidation(INVALID_VAL);
    expect(r.exitCode).toBe(1);
    expect(r.ok).toBe(false);
    expect(r.issues).toHaveLength(1);
    expect(r.issues[0]?.kind).toBe("answer-value-not-in-enum");
    expect(r.issues[0]?.path).toBe("stack.language");
    expect(r.errors).toHaveLength(0);
    expect(r.warnings.map((w) => w.path).sort()).toEqual([
      "identity.description",
      "identity.name",
      "identity.owner",
    ]);
  });

  it("exit 2 when the profile file is missing", async () => {
    const r = await runValidation("generator/__fixtures__/profiles/does-not-exist.yaml");
    expect(r.exitCode).toBe(2);
    expect(r.ok).toBe(false);
  });

  it("exit 2 when the YAML is malformed", async () => {
    const dir = mkdtempSync(join(tmpdir(), "run-"));
    const path = join(dir, "broken.yaml");
    writeFileSync(
      path,
      "version: '0.1.0'\nprofile:\n  name: x\n  description: y\nanswers:\n  foo: [unterminated",
    );
    const r = await runValidation(path);
    expect(r.exitCode).toBe(2);
  });
});

describe("formatReport", () => {
  it("renders OK for a zero-warnings, zero-errors result", async () => {
    const r = await runValidation(VALID);
    const report = formatReport({ ...r, warnings: [] }, VALID);
    expect(report).toMatch(/status: OK/);
  });

  it("renders WARN section for user-specific warnings", async () => {
    const r = await runValidation(VALID);
    const report = formatReport(r, VALID);
    expect(report).toMatch(/warning .*identity\.name/);
    expect(report).toMatch(/status: OK/);
  });

  it("renders FAIL with completeness error for missing required", async () => {
    const r = await runValidation(MISSING_REQ);
    const report = formatReport(r, MISSING_REQ);
    expect(report).toMatch(/status: FAIL/);
    expect(report).toMatch(/required-missing/);
    expect(report).toMatch(/domain\.type/);
  });

  it("renders FAIL with issue line for invalid enum value", async () => {
    const r = await runValidation(INVALID_VAL);
    const report = formatReport(r, INVALID_VAL);
    expect(report).toMatch(/status: FAIL/);
    expect(report).toMatch(/answer-value-not-in-enum/);
  });
});

describe("generator/run.ts CLI (integration)", () => {
  it("exits 0 for valid-partial and prints user-specific warnings", () => {
    const r = runCli(["--profile", VALID]);
    expect(r.code).toBe(0);
    expect(r.stdout).toMatch(/status: OK/);
    expect(r.stdout).toMatch(/identity\.name/);
  }, 30000);

  it("accepts --validate-only and still exits 0 for valid-partial", () => {
    const r = runCli(["--profile", VALID, "--validate-only"]);
    expect(r.code).toBe(0);
  }, 30000);

  it("exits 1 for missing-required fixture", () => {
    const r = runCli(["--profile", MISSING_REQ]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/required-missing/);
  }, 30000);

  it("exits 1 for invalid-value fixture", () => {
    const r = runCli(["--profile", INVALID_VAL]);
    expect(r.code).toBe(1);
    expect(r.stdout).toMatch(/answer-value-not-in-enum/);
  }, 30000);

  it("exits 2 with clear message when --out is passed (deferred to C1)", () => {
    const r = runCli(["--profile", VALID, "--out", "tmp/"]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/flag --out not supported in B3; planned for C1/);
  }, 30000);

  it("exits 2 with clear message when --dry-run is passed (deferred to C1)", () => {
    const r = runCli(["--profile", VALID, "--dry-run"]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/flag --dry-run not supported in B3; planned for C1/);
  }, 30000);

  it("exits 2 when --profile is missing", () => {
    const r = runCli([]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/--profile/);
  }, 30000);

  it("exits 2 when the profile file does not exist", () => {
    const r = runCli(["--profile", "generator/__fixtures__/profiles/does-not-exist.yaml"]);
    expect(r.code).toBe(2);
  }, 30000);

  it("exits 2 when an unknown flag is passed", () => {
    const r = runCli(["--profile", VALID, "--totally-unknown"]);
    expect(r.code).toBe(2);
  }, 30000);
});
