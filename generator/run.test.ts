import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { formatRenderSummary, formatReport, runRender, runValidation } from "./run.ts";

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

describe("runRender (unit)", () => {
  it("returns 18 FileWrite entries and user-specific warnings for valid-partial", async () => {
    const r = await runRender(VALID);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.files.map((f) => f.path).sort()).toEqual([
      ".claude/hooks/README.md",
      ".claude/rules/docs.md",
      ".claude/rules/patterns.md",
      ".claude/settings.json",
      ".claude/skills/README.md",
      ".github/workflows/ci.yml",
      "AGENTS.md",
      "CLAUDE.md",
      "HANDOFF.md",
      "MASTER_PLAN.md",
      "Makefile",
      "README.md",
      "ROADMAP.md",
      "docs/BRANCH_PROTECTION.md",
      "policy.yaml",
      "tests/README.md",
      "tests/smoke.test.ts",
      "vitest.config.ts",
    ]);
    for (const file of r.files) {
      expect(file.content.length).toBeGreaterThan(0);
    }
    expect(r.warnings.map((w) => w.path).sort()).toEqual([
      "identity.description",
      "identity.name",
      "identity.owner",
    ]);
  });

  it("returns an error when the profile file is missing", async () => {
    const r = await runRender("generator/__fixtures__/profiles/does-not-exist.yaml");
    expect(r.ok).toBe(false);
  });

  it("returns { ok: false, error } when a renderer throws (deferred framework), not a fatal crash", async () => {
    const dir = mkdtempSync(join(tmpdir(), "run-deferred-"));
    const path = join(dir, "profile.yaml");
    writeFileSync(
      path,
      [
        "version: \"0.1.0\"",
        "profile:",
        "  name: \"deferred-jest\"",
        "  description: \"deferred framework fixture\"",
        "answers:",
        "  \"domain.type\": \"cli\"",
        "  \"stack.language\": \"typescript\"",
        "  \"stack.database\": \"none\"",
        "  \"testing.unit_framework\": \"jest\"",
        "  \"testing.coverage_threshold\": 80",
        "  \"testing.e2e_framework\": \"none\"",
        "  \"workflow.ci_host\": \"github\"",
        "  \"workflow.release_strategy\": \"manual\"",
        "  \"workflow.branch_protection\": true",
        "  \"claude_code.default_model\": \"claude-sonnet-4-6\"",
        "",
      ].join("\n"),
    );
    const r = await runRender(path);
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.error).toMatch(/jest/);
    expect(r.error).toMatch(/deferred/i);
    expect(r.error).toMatch(/testing\.unit_framework/);
  });
});

describe("formatRenderSummary", () => {
  it("renders dry-run header + file list", async () => {
    const r = await runRender(VALID);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const out = formatRenderSummary(r.files, r.warnings, "dry-run");
    expect(out).toMatch(/dry-run.*18 file\(s\) would be emitted/);
    expect(out).toContain("CLAUDE.md");
    expect(out).toContain("policy.yaml");
    expect(out).toContain(".claude/rules/docs.md");
    expect(out).toContain(".claude/settings.json");
    expect(out).toContain(".claude/hooks/README.md");
    expect(out).toContain(".claude/skills/README.md");
    expect(out).toContain("tests/smoke.test.ts");
    expect(out).toContain("vitest.config.ts");
    expect(out).toContain("Makefile");
    expect(out).toContain(".github/workflows/ci.yml");
    expect(out).toContain("docs/BRANCH_PROTECTION.md");
    expect(out).toMatch(/warning .*identity\.name/);
  });

  it("renders write header with outDir", async () => {
    const r = await runRender(VALID);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const out = formatRenderSummary(r.files, r.warnings, "write", "/tmp/demo");
    expect(out).toMatch(/wrote 18 file\(s\) to \/tmp\/demo/);
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

  it("exits 0 and lists 18 files with --dry-run for valid-partial", () => {
    const r = runCli(["--profile", VALID, "--dry-run"]);
    expect(r.code).toBe(0);
    expect(r.stdout).toMatch(/dry-run.*18 file\(s\) would be emitted/);
    expect(r.stdout).toContain("CLAUDE.md");
    expect(r.stdout).toContain("MASTER_PLAN.md");
    expect(r.stdout).toContain("ROADMAP.md");
    expect(r.stdout).toContain("HANDOFF.md");
    expect(r.stdout).toContain("AGENTS.md");
    expect(r.stdout).toContain("README.md");
    expect(r.stdout).toContain("policy.yaml");
    expect(r.stdout).toContain(".claude/rules/docs.md");
    expect(r.stdout).toContain(".claude/rules/patterns.md");
    expect(r.stdout).toContain(".claude/settings.json");
    expect(r.stdout).toContain(".claude/hooks/README.md");
    expect(r.stdout).toContain(".claude/skills/README.md");
    expect(r.stdout).toContain("Makefile");
    expect(r.stdout).toContain("vitest.config.ts");
    expect(r.stdout).toContain("tests/README.md");
    expect(r.stdout).toContain("tests/smoke.test.ts");
    expect(r.stdout).toContain(".github/workflows/ci.yml");
    expect(r.stdout).toContain("docs/BRANCH_PROTECTION.md");
  }, 30000);

  it("exits 0 and writes 18 files into an empty --out directory", () => {
    const outDir = mkdtempSync(join(tmpdir(), "run-out-"));
    const r = runCli(["--profile", VALID, "--out", outDir]);
    expect(r.code).toBe(0);
    const written = readdirSync(outDir).sort();
    expect(written).toEqual([
      ".claude",
      ".github",
      "AGENTS.md",
      "CLAUDE.md",
      "HANDOFF.md",
      "MASTER_PLAN.md",
      "Makefile",
      "README.md",
      "ROADMAP.md",
      "docs",
      "policy.yaml",
      "tests",
      "vitest.config.ts",
    ]);
    expect(readFileSync(join(outDir, "CLAUDE.md"), "utf8").length).toBeGreaterThan(0);
    expect(readFileSync(join(outDir, ".claude/rules/docs.md"), "utf8"))
      .toContain("Trazabilidad de contexto");
    expect(readFileSync(join(outDir, "policy.yaml"), "utf8"))
      .toContain("type: \"generated-project\"");
    expect(readFileSync(join(outDir, "Makefile"), "utf8"))
      .toMatch(/^test:/m);
    expect(readFileSync(join(outDir, "vitest.config.ts"), "utf8"))
      .toContain("defineConfig");
    expect(readFileSync(join(outDir, "tests/smoke.test.ts"), "utf8"))
      .toMatch(/describe\s*\(/);
    expect(readFileSync(join(outDir, ".github/workflows/ci.yml"), "utf8"))
      .toMatch(/^name:\s*ci\s*$/m);
    expect(readFileSync(join(outDir, "docs/BRANCH_PROTECTION.md"), "utf8"))
      .toMatch(/Branch Protection/);
    const settingsRaw = readFileSync(join(outDir, ".claude/settings.json"), "utf8");
    const settings = JSON.parse(settingsRaw) as Record<string, unknown>;
    expect(settings.hooks).toEqual({});
    expect(typeof settings._note).toBe("string");
    expect(readFileSync(join(outDir, ".claude/hooks/README.md"), "utf8"))
      .toMatch(/Fase\s*D/);
    expect(readFileSync(join(outDir, ".claude/skills/README.md"), "utf8"))
      .toMatch(/Fase\s*E/);
    expect(r.stdout).toMatch(/wrote 18 file\(s\)/);
  }, 30000);

  it("exits 3 when --out target is not empty", () => {
    const outDir = mkdtempSync(join(tmpdir(), "run-out-"));
    writeFileSync(join(outDir, "pre-existing.txt"), "hi");
    const r = runCli(["--profile", VALID, "--out", outDir]);
    expect(r.code).toBe(3);
    expect(r.stderr).toMatch(/not empty/);
  }, 30000);

  it("exits 2 when --out target is a file (not a directory)", () => {
    const parent = mkdtempSync(join(tmpdir(), "run-out-"));
    const filePath = join(parent, "iam-a-file.txt");
    writeFileSync(filePath, "hi");
    const r = runCli(["--profile", VALID, "--out", filePath]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/not a directory/);
  }, 30000);

  it("exits 2 when --validate-only and --dry-run are combined", () => {
    const r = runCli(["--profile", VALID, "--validate-only", "--dry-run"]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/mutually exclusive/);
  }, 30000);

  it("exits 2 when --out and --dry-run are combined", () => {
    const outDir = mkdtempSync(join(tmpdir(), "run-out-"));
    const r = runCli(["--profile", VALID, "--out", outDir, "--dry-run"]);
    expect(r.code).toBe(2);
    expect(r.stderr).toMatch(/mutually exclusive/);
  }, 30000);

  it("exits 1 without rendering when profile has validation errors", () => {
    const r = runCli(["--profile", MISSING_REQ, "--dry-run"]);
    expect(r.code).toBe(1);
    expect(r.stdout).not.toMatch(/would be emitted/);
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
