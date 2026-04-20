import { z } from "zod";
import type { SchemaFile } from "./meta-schema.ts";

export type ProfileIssueKind =
  | "answer-unknown-path"
  | "answer-type-mismatch"
  | "answer-value-not-in-enum"
  | "answer-array-item-type-mismatch"
  | "answer-constraint-violation";

export type ProfileIssue = {
  kind: ProfileIssueKind;
  path: string;
  detail: string;
};

const ProfileFile = z
  .object({
    version: z.string().regex(/^\d+\.\d+\.\d+$/, "version must be semver"),
    profile: z
      .object({
        name: z.string().min(1),
        description: z.string().min(1),
      })
      .strict(),
    answers: z.record(z.string(), z.unknown()),
  })
  .strict();

export type ProfileFile = z.infer<typeof ProfileFile>;

export function parseProfileFile(input: unknown): ProfileFile {
  const result = ProfileFile.safeParse(input);
  if (!result.success) {
    throw new Error(`profile invalid: ${formatZod(result.error)}`);
  }
  return result.data;
}

type Field = SchemaFile["sections"][number]["fields"][number];

export function validateProfile(schema: SchemaFile, profile: ProfileFile): ProfileIssue[] {
  const fieldByPath = new Map<string, Field>();
  for (const section of schema.sections) {
    for (const field of section.fields) {
      fieldByPath.set(field.path, field);
    }
  }

  const issues: ProfileIssue[] = [];
  for (const [path, value] of Object.entries(profile.answers)) {
    const field = fieldByPath.get(path);
    if (!field) {
      issues.push({
        kind: "answer-unknown-path",
        path,
        detail: `path '${path}' is not declared in schema`,
      });
      continue;
    }
    validateAnswer(path, value, field, issues);
  }
  return issues;
}

function validateAnswer(path: string, value: unknown, field: Field, issues: ProfileIssue[]): void {
  switch (field.type) {
    case "string":
      if (typeof value !== "string") {
        issues.push(typeMismatch(path, field.type, value));
        return;
      }
      if (field.pattern !== undefined && !new RegExp(field.pattern).test(value)) {
        issues.push(violation(path, `value '${value}' does not match pattern /${field.pattern}/`));
      }
      if (field.minLength !== undefined && value.length < field.minLength) {
        issues.push(violation(path, `length ${value.length} below minLength ${field.minLength}`));
      }
      if (field.maxLength !== undefined && value.length > field.maxLength) {
        issues.push(violation(path, `length ${value.length} above maxLength ${field.maxLength}`));
      }
      return;

    case "number":
      if (typeof value !== "number") {
        issues.push(typeMismatch(path, field.type, value));
        return;
      }
      if (field.min !== undefined && value < field.min) {
        issues.push(violation(path, `value ${value} below min ${field.min}`));
      }
      if (field.max !== undefined && value > field.max) {
        issues.push(violation(path, `value ${value} above max ${field.max}`));
      }
      return;

    case "boolean":
      if (typeof value !== "boolean") {
        issues.push(typeMismatch(path, field.type, value));
      }
      return;

    case "enum":
      if (!field.values.includes(value as string | number | boolean)) {
        issues.push({
          kind: "answer-value-not-in-enum",
          path,
          detail: `value '${String(value)}' not in enum values [${field.values.map((v) => String(v)).join(", ")}]`,
        });
      }
      return;

    case "array":
      if (!Array.isArray(value)) {
        issues.push(typeMismatch(path, field.type, value));
        return;
      }
      for (const [idx, item] of value.entries()) {
        if (typeof item !== field.items) {
          issues.push({
            kind: "answer-array-item-type-mismatch",
            path,
            detail: `item[${idx}] '${String(item)}' is ${typeof item}, expected ${field.items}`,
          });
        }
      }
      if (field.minItems !== undefined && value.length < field.minItems) {
        issues.push(violation(path, `has ${value.length} items, below minItems ${field.minItems}`));
      }
      if (field.maxItems !== undefined && value.length > field.maxItems) {
        issues.push(violation(path, `has ${value.length} items, above maxItems ${field.maxItems}`));
      }
      return;
  }
}

function typeMismatch(path: string, expected: Field["type"], value: unknown): ProfileIssue {
  return {
    kind: "answer-type-mismatch",
    path,
    detail: `expected ${expected}, got ${Array.isArray(value) ? "array" : typeof value}`,
  };
}

function violation(path: string, detail: string): ProfileIssue {
  return { kind: "answer-constraint-violation", path, detail };
}

function formatZod(err: z.ZodError): string {
  return err.issues.map((i) => `  at ${i.path.join(".") || "<root>"}: ${i.message}`).join("\n");
}
