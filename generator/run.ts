#!/usr/bin/env tsx
import { parseArgs } from "node:util";
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

const SCHEMA_PATH = "questionnaire/schema.yaml";
const DEFERRED_FLAG_MSG = (flag: string) => `flag --${flag} not supported in B3; planned for C1`;

type ExitCode = 0 | 1 | 2;

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

  if (values.out !== undefined) {
    process.stderr.write(`generator/run: ${DEFERRED_FLAG_MSG("out")}\n`);
    process.exit(2);
  }
  if (values["dry-run"] !== undefined) {
    process.stderr.write(`generator/run: ${DEFERRED_FLAG_MSG("dry-run")}\n`);
    process.exit(2);
  }
  if (!values.profile) {
    process.stderr.write(
      "generator/run: --profile <path> is required. Usage: generator/run.ts --profile <path> [--validate-only]\n",
    );
    process.exit(2);
  }

  const result = await runValidation(values.profile);
  process.stdout.write(formatReport(result, values.profile) + "\n");
  process.exit(result.exitCode);
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
