#!/usr/bin/env tsx
import { parseArgs } from "node:util";
import { stat } from "node:fs/promises";
import { readAndParseYaml, errorMessage } from "../tools/lib/read-yaml.ts";
import { loadProfile } from "./lib/profile-loader.ts";
import {
  parseSchemaFile,
  validateProfile,
  type ProfileIssue,
  type SchemaFile,
} from "./lib/schema.ts";
import {
  completenessCheck,
  type CompletenessEntry,
} from "./lib/validators.ts";
import { buildProfile } from "./lib/profile-model.ts";
import {
  isDirEmpty,
  renderAll,
  writeFiles,
  type FileWrite,
} from "./lib/render-pipeline.ts";
import { allRenderers } from "./renderers/index.ts";

const SCHEMA_PATH = "questionnaire/schema.yaml";

type ExitCode = 0 | 1 | 2 | 3;

export type Mode = "validate-only" | "dry-run" | "write";

export type RunResult = {
  ok: boolean;
  issues: ProfileIssue[];
  errors: CompletenessEntry[];
  warnings: CompletenessEntry[];
  parseErrors: string[];
  exitCode: ExitCode;
};

export async function runValidation(profilePath: string): Promise<RunResult> {
  const schema = await loadSchema(SCHEMA_PATH);
  if (!schema.ok) {
    return empty({ parseErrors: [schema.error], exitCode: 2 });
  }

  const loaded = await loadProfile(profilePath);
  if (!loaded.ok) {
    const exitCode: ExitCode = loaded.error.startsWith("profile invalid") ? 1 : 2;
    return empty({ parseErrors: [loaded.error], exitCode });
  }

  const issues = validateProfile(schema.value, loaded.profile);
  const completeness = completenessCheck(schema.value, loaded.profile);
  const hasBlocking = issues.length > 0 || completeness.errors.length > 0;

  return {
    ok: !hasBlocking,
    issues,
    errors: completeness.errors,
    warnings: completeness.warnings,
    parseErrors: [],
    exitCode: hasBlocking ? 1 : 0,
  };
}

export async function runRender(profilePath: string): Promise<
  | { ok: true; files: FileWrite[]; warnings: CompletenessEntry[] }
  | { ok: false; error: string }
> {
  const loaded = await loadProfile(profilePath);
  if (!loaded.ok) {
    return { ok: false, error: loaded.error };
  }
  const schema = await loadSchema(SCHEMA_PATH);
  if (!schema.ok) {
    return { ok: false, error: schema.error };
  }
  const { warnings } = completenessCheck(schema.value, loaded.profile);
  const profile = buildProfile(loaded.profile);
  let files: FileWrite[];
  try {
    files = renderAll(profile, [...allRenderers]);
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
  return { ok: true, files, warnings };
}

export function formatReport(result: RunResult, profilePath: string): string {
  const lines: string[] = [];
  lines.push(`generator/run:`);
  lines.push(`  schema:  ${SCHEMA_PATH}`);
  lines.push(`  profile: ${profilePath}`);
  if (result.ok) {
    lines.push(`  status: OK`);
  } else {
    lines.push(`  status: FAIL`);
  }
  for (const err of result.parseErrors) {
    lines.push(`  error: ${err}`);
  }
  for (const err of result.errors) {
    lines.push(`  error [required-missing] ${err.path}: ${err.detail}`);
  }
  for (const issue of result.issues) {
    lines.push(`  issue [${issue.kind}] ${issue.path}: ${issue.detail}`);
  }
  for (const warn of result.warnings) {
    lines.push(`  warning [user-specific-missing] ${warn.path}: ${warn.detail}`);
  }
  return lines.join("\n");
}

export function formatRenderSummary(
  files: FileWrite[],
  warnings: CompletenessEntry[],
  mode: "dry-run",
): string;
export function formatRenderSummary(
  files: FileWrite[],
  warnings: CompletenessEntry[],
  mode: "write",
  outDir: string,
): string;
export function formatRenderSummary(
  files: FileWrite[],
  warnings: CompletenessEntry[],
  mode: "dry-run" | "write",
  outDir?: string,
): string {
  const lines: string[] = [];
  if (mode === "dry-run") {
    lines.push(`generator/render [dry-run]: ${files.length} file(s) would be emitted:`);
  } else {
    if (outDir === undefined) {
      throw new Error(
        "formatRenderSummary: outDir is required when mode === 'write'",
      );
    }
    lines.push(`generator/render [write]: wrote ${files.length} file(s) to ${outDir}:`);
  }
  for (const file of files) {
    lines.push(`  ${file.path} (${file.content.length} bytes)`);
  }
  for (const warn of warnings) {
    lines.push(`  warning [user-specific-missing] ${warn.path}: ${warn.detail}`);
  }
  return lines.join("\n");
}

type SchemaLoad = { ok: true; value: SchemaFile } | { ok: false; error: string };

async function loadSchema(path: string): Promise<SchemaLoad> {
  const read = await readAndParseYaml(path);
  if (!read.ok) return { ok: false, error: read.error };
  try {
    return { ok: true, value: parseSchemaFile(read.value) };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

function empty(partial: { parseErrors: string[]; exitCode: ExitCode }): RunResult {
  return {
    ok: false,
    issues: [],
    errors: [],
    warnings: [],
    parseErrors: partial.parseErrors,
    exitCode: partial.exitCode,
  };
}

/* v8 ignore start */
async function main(): Promise<void> {
  let parsed;
  try {
    parsed = parseArgs({
      options: {
        profile: { type: "string" },
        "validate-only": { type: "boolean" },
        out: { type: "string" },
        "dry-run": { type: "boolean" },
      },
      strict: true,
      allowPositionals: false,
    });
  } catch (err) {
    process.stderr.write(`generator/run: ${errorMessage(err)}\n`);
    process.exit(2);
  }

  const { values } = parsed;
  const profilePath = values.profile;
  const validateOnly = values["validate-only"] === true;
  const dryRun = values["dry-run"] === true;
  const outDir = values.out;

  if (!profilePath) {
    process.stderr.write(
      "generator/run: --profile <path> is required. " +
        "Usage: generator/run.ts --profile <path> [--validate-only | --dry-run | --out <dir>]\n",
    );
    process.exit(2);
  }

  const modes = [validateOnly, dryRun, outDir !== undefined].filter(Boolean).length;
  if (modes > 1) {
    process.stderr.write(
      "generator/run: --validate-only, --dry-run and --out are mutually exclusive\n",
    );
    process.exit(2);
  }

  const validation = await runValidation(profilePath);
  process.stdout.write(formatReport(validation, profilePath) + "\n");
  if (!validation.ok) {
    process.exit(validation.exitCode);
  }

  const mode: Mode = outDir !== undefined ? "write" : dryRun ? "dry-run" : "validate-only";
  if (mode === "validate-only") {
    process.exit(0);
  }

  if (mode === "write" && outDir !== undefined) {
    try {
      const s = await stat(outDir);
      if (!s.isDirectory()) {
        process.stderr.write(
          `generator/run: --out target '${outDir}' is not a directory; aborting (exit 2)\n`,
        );
        process.exit(2);
      }
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code !== "ENOENT") {
        process.stderr.write(
          `generator/run: cannot stat --out target '${outDir}': ${errorMessage(err)}\n`,
        );
        process.exit(2);
      }
    }
    if (!(await isDirEmpty(outDir))) {
      process.stderr.write(
        `generator/run: --out target '${outDir}' is not empty; aborting (exit 3)\n`,
      );
      process.exit(3);
    }
  }

  const rendered = await runRender(profilePath);
  if (!rendered.ok) {
    process.stderr.write(`generator/run: render failed: ${rendered.error}\n`);
    process.exit(2);
  }

  if (mode === "write" && outDir !== undefined) {
    await writeFiles(outDir, rendered.files);
    process.stdout.write(
      formatRenderSummary(rendered.files, rendered.warnings, "write", outDir) + "\n",
    );
  } else {
    process.stdout.write(
      formatRenderSummary(rendered.files, rendered.warnings, "dry-run") + "\n",
    );
  }
  process.exit(0);
}

const isDirectRun = (() => {
  const entry = process.argv[1];
  if (!entry) return false;
  return entry.endsWith("generator/run.ts") || entry.endsWith("generator/run.js");
})();

if (isDirectRun) {
  main().catch((err) => {
    process.stderr.write(`generator/run: fatal: ${errorMessage(err)}\n`);
    process.exit(2);
  });
}
/* v8 ignore stop */
