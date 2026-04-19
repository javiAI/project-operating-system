import { collectPaths, parseCondition } from "./condition-parser.ts";
import type { QuestionsFile, SchemaFile } from "./meta-schema.ts";

export type CrossValidationIssue = {
  kind:
    | "maps_to-unknown-path"
    | "required-uncovered"
    | "section-unknown"
    | "option-outside-enum"
    | "question-field-type-mismatch"
    | "question-section-mismatch"
    | "when-unknown-path";
  where: string;
  detail: string;
};

type Field = SchemaFile["sections"][number]["fields"][number];
type NonInfoQuestionType = "text" | "number" | "bool" | "single" | "multi";

const QUESTION_TO_FIELD_TYPE: Record<NonInfoQuestionType, Field["type"]> = {
  text: "string",
  number: "number",
  bool: "boolean",
  single: "enum",
  multi: "array",
};

export function crossValidate(schema: SchemaFile, questions: QuestionsFile): CrossValidationIssue[] {
  const issues: CrossValidationIssue[] = [];
  const fieldByPath = new Map<string, Field>();
  const sectionByFieldPath = new Map<string, string>();
  const sectionIds = new Set<string>();

  for (const section of schema.sections) {
    sectionIds.add(section.id);
    for (const field of section.fields) {
      fieldByPath.set(field.path, field);
      sectionByFieldPath.set(field.path, section.id);
    }
  }

  const coveredPaths = new Set<string>();

  for (const q of questions.questions) {
    const sectionKnown = sectionIds.has(q.section);
    if (!sectionKnown) {
      issues.push({
        kind: "section-unknown",
        where: q.id,
        detail: `question references section '${q.section}' not declared in schema`,
      });
    }

    if (q.when !== undefined) {
      try {
        const ast = parseCondition(q.when);
        for (const p of collectPaths(ast)) {
          if (!fieldByPath.has(p)) {
            issues.push({
              kind: "when-unknown-path",
              where: q.id,
              detail: `when references unknown path '${p}'`,
            });
          }
        }
      } catch {
        // syntactic errors are surfaced by meta-schema; skip here.
      }
    }

    if (q.type === "info") continue;

    const field = fieldByPath.get(q.maps_to);
    if (!field) {
      issues.push({
        kind: "maps_to-unknown-path",
        where: q.id,
        detail: `maps_to '${q.maps_to}' does not match any field in schema`,
      });
      continue;
    }

    coveredPaths.add(q.maps_to);

    const expectedFieldType = QUESTION_TO_FIELD_TYPE[q.type];
    if (field.type !== expectedFieldType) {
      issues.push({
        kind: "question-field-type-mismatch",
        where: q.id,
        detail: `question type '${q.type}' expects field type '${expectedFieldType}' but '${field.path}' is '${field.type}'`,
      });
    }

    if (sectionKnown) {
      const fieldSection = sectionByFieldPath.get(field.path);
      if (fieldSection && fieldSection !== q.section) {
        issues.push({
          kind: "question-section-mismatch",
          where: q.id,
          detail: `question is in section '${q.section}' but field '${field.path}' lives in section '${fieldSection}'`,
        });
      }
    }

    if ((q.type === "single" || q.type === "multi") && field.type === "enum") {
      for (const opt of q.options) {
        if (!field.values.includes(opt.value as string | number | boolean)) {
          issues.push({
            kind: "option-outside-enum",
            where: q.id,
            detail: `option value '${String(opt.value)}' is not in enum values of '${field.path}'`,
          });
        }
      }
    }
  }

  for (const [path, field] of fieldByPath) {
    if (!field.required) continue;
    if (coveredPaths.has(path)) continue;
    if ("default" in field && field.default !== undefined) continue;
    issues.push({
      kind: "required-uncovered",
      where: path,
      detail: `required field '${path}' has no question and no default`,
    });
  }

  return issues;
}
