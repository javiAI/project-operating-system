import type { ProfileFile, SchemaFile } from "./schema.ts";

export const USER_SPECIFIC_PATHS = [
  "identity.name",
  "identity.description",
  "identity.owner",
] as const;

export type CompletenessEntry = { path: string; detail: string };

export type CompletenessResult = {
  errors: CompletenessEntry[];
  warnings: CompletenessEntry[];
};

type Field = SchemaFile["sections"][number]["fields"][number];

export function completenessCheck(schema: SchemaFile, profile: ProfileFile): CompletenessResult {
  const answers = profile.answers;
  const errors: CompletenessEntry[] = [];
  const warnings: CompletenessEntry[] = [];

  for (const section of schema.sections) {
    for (const field of section.fields) {
      if (!field.required) continue;
      if (Object.prototype.hasOwnProperty.call(answers, field.path)) continue;
      if (hasDefault(field)) continue;

      const entry: CompletenessEntry = {
        path: field.path,
        detail: `required path '${field.path}' not present in profile.answers`,
      };
      if ((USER_SPECIFIC_PATHS as readonly string[]).includes(field.path)) {
        warnings.push(entry);
      } else {
        errors.push(entry);
      }
    }
  }

  return { errors, warnings };
}

function hasDefault(field: Field): boolean {
  return "default" in field && field.default !== undefined;
}
