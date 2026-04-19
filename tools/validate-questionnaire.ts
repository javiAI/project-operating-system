#!/usr/bin/env tsx
import { readFile } from "node:fs/promises";
import { parseArgs } from "node:util";
import { parse as parseYaml } from "yaml";
import { crossValidate, type CrossValidationIssue } from "./lib/cross-validate.ts";
import { parseQuestionsFile, parseSchemaFile } from "./lib/meta-schema.ts";

type ExitCode = 0 | 1 | 2;

export type ValidationResult = {
  ok: boolean;
  issues: CrossValidationIssue[];
  errors: string[];
  exitCode: ExitCode;
};

export async function validateQuestionnaire(
  schemaPath: string,
  questionsPath: string
): Promise<ValidationResult> {
  const errors: string[] = [];

  const schemaRead = await readAndParseYaml(schemaPath);
  if (!schemaRead.ok) {
    return { ok: false, issues: [], errors: [schemaRead.error], exitCode: 2 };
  }

  const questionsRead = await readAndParseYaml(questionsPath);
  if (!questionsRead.ok) {
    return { ok: false, issues: [], errors: [questionsRead.error], exitCode: 2 };
  }

  try {
    const schema = parseSchemaFile(schemaRead.value);
    const questions = parseQuestionsFile(questionsRead.value);
    const issues = crossValidate(schema, questions);
    return { ok: issues.length === 0, issues, errors: [], exitCode: issues.length === 0 ? 0 : 1 };
  } catch (err) {
    errors.push(errorMessage(err));
    return { ok: false, issues: [], errors, exitCode: 1 };
  }
}

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

async function readAndParseYaml(
  path: string
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

export function formatReport(result: ValidationResult, schemaPath: string, questionsPath: string): string {
  const lines: string[] = [];
  lines.push(`validate-questionnaire:`);
  lines.push(`  schema:    ${schemaPath}`);
  lines.push(`  questions: ${questionsPath}`);
  if (result.ok) {
    lines.push(`  status: OK`);
    return lines.join("\n");
  }
  lines.push(`  status: FAIL`);
  for (const err of result.errors) {
    lines.push(`  error: ${err}`);
  }
  for (const issue of result.issues) {
    lines.push(`  issue [${issue.kind}] ${issue.where}: ${issue.detail}`);
  }
  return lines.join("\n");
}

/* v8 ignore start */
async function main(): Promise<void> {
  const { values } = parseArgs({
    options: {
      schema: { type: "string", short: "s", default: "questionnaire/schema.yaml" },
      questions: { type: "string", short: "q", default: "questionnaire/questions.yaml" },
    },
  });

  const schemaPath = values.schema as string;
  const questionsPath = values.questions as string;
  const result = await validateQuestionnaire(schemaPath, questionsPath);
  process.stdout.write(formatReport(result, schemaPath, questionsPath) + "\n");
  process.exit(result.exitCode);
}

const isDirectRun = (() => {
  const entry = process.argv[1];
  if (!entry) return false;
  return entry.endsWith("validate-questionnaire.ts") || entry.endsWith("validate-questionnaire.js");
})();

if (isDirectRun) {
  main().catch((err) => {
    process.stderr.write(`validate-questionnaire: fatal: ${(err as Error).message}\n`);
    process.exit(2);
  });
}
/* v8 ignore stop */
