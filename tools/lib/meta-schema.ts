import { z } from "zod";
import { parseCondition } from "./condition-parser.ts";

const PATH_RE = /^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$/;
const ID_RE = /^[a-z][a-z0-9_]*$/;
const SECTION_ID_RE = /^[A-G]$/;

const FieldCommon = z.object({
  path: z.string().regex(PATH_RE, "path must be snake_case dotted (e.g. identity.name)"),
  description: z.string().optional(),
  required: z.boolean().optional(),
});

const compilableRegex = z.string().refine(
  (p) => {
    try {
      new RegExp(p);
      return true;
    } catch {
      return false;
    }
  },
  { message: "pattern must be a valid regex" },
);

const StringField = FieldCommon.extend({
  type: z.literal("string"),
  default: z.string().optional(),
  pattern: compilableRegex.optional(),
  minLength: z.number().int().nonnegative().optional(),
  maxLength: z.number().int().positive().optional(),
});

const NumberField = FieldCommon.extend({
  type: z.literal("number"),
  default: z.number().optional(),
  min: z.number().optional(),
  max: z.number().optional(),
});

const BooleanField = FieldCommon.extend({
  type: z.literal("boolean"),
  default: z.boolean().optional(),
});

const EnumField = FieldCommon.extend({
  type: z.literal("enum"),
  values: z.array(z.union([z.string(), z.number(), z.boolean()])).min(1, "enum needs at least one value"),
  default: z.union([z.string(), z.number(), z.boolean()]).optional(),
});

const ArrayField = FieldCommon.extend({
  type: z.literal("array"),
  items: z.enum(["string", "number", "boolean"]),
  values: z.array(z.union([z.string(), z.number(), z.boolean()])).min(1, "array values allowlist needs at least one entry").optional(),
  default: z.array(z.union([z.string(), z.number(), z.boolean()])).optional(),
  minItems: z.number().int().nonnegative().optional(),
  maxItems: z.number().int().positive().optional(),
});

const Field = z.discriminatedUnion("type", [
  StringField,
  NumberField,
  BooleanField,
  EnumField,
  ArrayField,
]);

const Section = z.object({
  id: z.string().regex(SECTION_ID_RE, "section id must be single uppercase letter A-G"),
  name: z.string().min(1),
  description: z.string().optional(),
  fields: z.array(Field).min(1, "section must have at least one field"),
});

const SchemaFile = z.object({
  version: z.string().regex(/^\d+\.\d+\.\d+$/, "version must be semver"),
  sections: z.array(Section).min(1, "schema needs at least one section"),
}).superRefine((doc, ctx) => {
  const seen = new Map<string, string>();
  for (const section of doc.sections) {
    for (const field of section.fields) {
      const prev = seen.get(field.path);
      if (prev) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `duplicate field path '${field.path}' (already in section ${prev})`,
          path: ["sections"],
        });
      } else {
        seen.set(field.path, section.id);
      }
      if (field.type === "enum" && field.default !== undefined && !field.values.includes(field.default)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `enum field '${field.path}' default '${String(field.default)}' not in values`,
          path: ["sections"],
        });
      }
      if (field.type === "array") {
        if (field.default !== undefined) {
          for (const [idx, val] of field.default.entries()) {
            const expected = field.items;
            const ok =
              (expected === "string" && typeof val === "string") ||
              (expected === "number" && typeof val === "number") ||
              (expected === "boolean" && typeof val === "boolean");
            if (!ok) {
              ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: `array field '${field.path}' default[${idx}] must be ${expected}`,
                path: ["sections"],
              });
            }
            if (field.values !== undefined && !field.values.includes(val as string | number | boolean)) {
              ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: `array field '${field.path}' default[${idx}] '${String(val)}' not in values allowlist`,
                path: ["sections"],
              });
            }
          }
          if (field.minItems !== undefined && field.default.length < field.minItems) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: `array field '${field.path}' default has ${field.default.length} items, below minItems ${field.minItems}`,
              path: ["sections"],
            });
          }
          if (field.maxItems !== undefined && field.default.length > field.maxItems) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: `array field '${field.path}' default has ${field.default.length} items, above maxItems ${field.maxItems}`,
              path: ["sections"],
            });
          }
        }
      }
    }
  }
});

export type SchemaFile = z.infer<typeof SchemaFile>;

const QuestionOption = z.object({
  value: z.union([z.string(), z.number(), z.boolean()]),
  label: z.string().optional(),
});

const QuestionCommon = z.object({
  id: z.string().regex(ID_RE, "question id must be snake_case"),
  section: z.string().regex(SECTION_ID_RE),
  text: z.string().min(1),
  description: z.string().optional(),
  when: z.string().optional(),
});

const TextQuestion = QuestionCommon.extend({
  type: z.literal("text"),
  maps_to: z.string().regex(PATH_RE, "maps_to must be snake_case dotted path"),
  validation: z
    .object({
      pattern: compilableRegex.optional(),
      minLength: z.number().int().nonnegative().optional(),
      maxLength: z.number().int().positive().optional(),
    })
    .optional(),
});

const NumberQuestion = QuestionCommon.extend({
  type: z.literal("number"),
  maps_to: z.string().regex(PATH_RE),
  min: z.number().optional(),
  max: z.number().optional(),
});

const BooleanQuestion = QuestionCommon.extend({
  type: z.literal("bool"),
  maps_to: z.string().regex(PATH_RE),
  default: z.boolean().optional(),
});

const SingleQuestion = QuestionCommon.extend({
  type: z.literal("single"),
  maps_to: z.string().regex(PATH_RE),
  options: z.array(QuestionOption).min(1, "single needs ≥1 option"),
});

const MultiQuestion = QuestionCommon.extend({
  type: z.literal("multi"),
  maps_to: z.string().regex(PATH_RE),
  options: z.array(QuestionOption).min(1),
});

const InfoQuestion = QuestionCommon.extend({
  type: z.literal("info"),
});

const Question = z.discriminatedUnion("type", [
  TextQuestion,
  NumberQuestion,
  BooleanQuestion,
  SingleQuestion,
  MultiQuestion,
  InfoQuestion,
]);

const QuestionsFile = z.object({
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
  questions: z.array(Question).min(1),
}).superRefine((doc, ctx) => {
  const ids = new Set<string>();
  for (const q of doc.questions) {
    if (ids.has(q.id)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `duplicate question id '${q.id}'`,
        path: ["questions"],
      });
    }
    ids.add(q.id);
    if (q.when !== undefined) {
      try {
        parseCondition(q.when);
      } catch (err) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `invalid 'when' expression on question '${q.id}': ${(err as Error).message}`,
          path: ["questions"],
        });
      }
    }
  }
});

export type QuestionsFile = z.infer<typeof QuestionsFile>;

export function parseSchemaFile(input: unknown): SchemaFile {
  const result = SchemaFile.safeParse(input);
  if (!result.success) {
    throw new Error(`schema.yaml invalid: ${formatZod(result.error)}`);
  }
  return result.data;
}

export function parseQuestionsFile(input: unknown): QuestionsFile {
  const result = QuestionsFile.safeParse(input);
  if (!result.success) {
    throw new Error(`questions.yaml invalid: ${formatZod(result.error)}`);
  }
  return result.data;
}

function formatZod(err: z.ZodError): string {
  return err.issues
    .map((i) => `  at ${i.path.join(".") || "<root>"}: ${i.message}`)
    .join("\n");
}

export { SchemaFile as SchemaFileZ, QuestionsFile as QuestionsFileZ };
