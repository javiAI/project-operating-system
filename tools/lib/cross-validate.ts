import type { QuestionsFile, SchemaFile } from "./meta-schema.ts";

export type CrossValidationIssue = {
  kind:
    | "maps_to-unknown-path"
    | "required-uncovered"
    | "section-unknown"
    | "option-outside-enum";
  where: string;
  detail: string;
};

export function crossValidate(schema: SchemaFile, questions: QuestionsFile): CrossValidationIssue[] {
  const issues: CrossValidationIssue[] = [];
  const fieldByPath = new Map<string, SchemaFile["sections"][number]["fields"][number]>();
  const sectionIds = new Set<string>();

  for (const section of schema.sections) {
    sectionIds.add(section.id);
    for (const field of section.fields) {
      fieldByPath.set(field.path, field);
    }
  }

  const coveredPaths = new Set<string>();

  for (const q of questions.questions) {
    if (!sectionIds.has(q.section)) {
      issues.push({
        kind: "section-unknown",
        where: q.id,
        detail: `question references section '${q.section}' not declared in schema`,
      });
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
