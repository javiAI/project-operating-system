#!/usr/bin/env tsx
import { readFile } from "node:fs/promises";
import { parseArgs } from "node:util";
import { parse as parseYaml } from "yaml";
import { parseSchemaFile } from "./lib/meta-schema.ts";
import {
  parseProfileFile,
  validateProfile,
  type ProfileIssue,
} from "./lib/profile-validator.ts";

type ExitCode = 0 | 1 | 2;

export type ValidationResult = {
  ok: boolean;
  issues: ProfileIssue[];
  errors: string[];
  exitCode: ExitCode;
};

export async function validateProfileFile(
  schemaPath: string,
  profilePath: string,
): Promise<ValidationResult> {
  const schemaRead = await readAndParseYaml(schemaPath);
  if (!schemaRead.ok) {
    return { ok: false, issues: [], errors: [schemaRead.error], exitCode: 2 };
  }

  const profileRead = await readAndParseYaml(profilePath);
  if (!profileRead.ok) {
    return { ok: false, issues: [], errors: [profileRead.error], exitCode: 2 };
  }

  try {
    const schema = parseSchemaFile(schemaRead.value);
    const profile = parseProfileFile(profileRead.value);
    const issues = validateProfile(schema, profile);
    return {
      ok: issues.length === 0,
      issues,
      errors: [],
      exitCode: issues.length === 0 ? 0 : 1,
    };
  } catch (err) {
    return { ok: false, issues: [], errors: [errorMessage(err)], exitCode: 1 };
  }
}

export function formatReport(result: ValidationResult, schemaPath: string, profilePath: string): string {
  const lines: string[] = [];
  lines.push(`validate-profile:`);
  lines.push(`  schema:  ${schemaPath}`);
  lines.push(`  profile: ${profilePath}`);
  if (result.ok) {
    lines.push(`  status: OK`);
    return lines.join("\n");
  }
  lines.push(`  status: FAIL`);
  for (const err of result.errors) {
    lines.push(`  error: ${err}`);
  }
  for (const issue of result.issues) {
    lines.push(`  issue [${issue.kind}] ${issue.path}: ${issue.detail}`);
  }
  return lines.join("\n");
}

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

async function readAndParseYaml(
  path: string,
): Promise<{ ok: true; value: unknown } | { ok: false; error: string }> {
  let raw: string;
  try {
    raw = await readFile(path, "utf8");
  } catch (err) {
    return { ok: false, error: `cannot read ${path}: ${errorMessage(err)}` };
  }
  try {
    return { ok: true, value: parseYaml(raw) };
  } catch (err) {
    return { ok: false, error: `cannot parse ${path}: ${errorMessage(err)}` };
  }
}

/* v8 ignore start */
async function main(): Promise<void> {
  const { values, positionals } = parseArgs({
    options: {
      schema: { type: "string", short: "s", default: "questionnaire/schema.yaml" },
      profile: { type: "string", short: "p" },
    },
    allowPositionals: true,
  });

  const schemaPath = values.schema as string;
  const profilePath = (values.profile as string | undefined) ?? positionals[0];
  if (!profilePath) {
    process.stderr.write(
      "validate-profile: no profile path given. Usage: validate-profile <profile.yaml> [--schema schema.yaml]\n",
    );
    process.exit(2);
  }

  const result = await validateProfileFile(schemaPath, profilePath);
  process.stdout.write(formatReport(result, schemaPath, profilePath) + "\n");
  process.exit(result.exitCode);
}

const isDirectRun = (() => {
  const entry = process.argv[1];
  if (!entry) return false;
  return entry.endsWith("validate-profile.ts") || entry.endsWith("validate-profile.js");
})();

if (isDirectRun) {
  main().catch((err) => {
    process.stderr.write(`validate-profile: fatal: ${(err as Error).message}\n`);
    process.exit(2);
  });
}
/* v8 ignore stop */
