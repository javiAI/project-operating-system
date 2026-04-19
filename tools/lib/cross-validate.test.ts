import { describe, expect, it } from "vitest";
import { crossValidate } from "./cross-validate.ts";
import { parseQuestionsFile, parseSchemaFile } from "./meta-schema.ts";

const baseSchema = parseSchemaFile({
  version: "0.1.0",
  sections: [
    {
      id: "A",
      name: "Identity",
      fields: [
        { path: "identity.name", type: "string", required: true },
        { path: "identity.license", type: "enum", values: ["MIT", "Apache-2.0"], default: "MIT" },
      ],
    },
    {
      id: "C",
      name: "Stack",
      fields: [
        { path: "stack.language", type: "enum", values: ["typescript", "python"], required: true },
        { path: "stack.coverage", type: "number", default: 80 },
      ],
    },
  ],
});

describe("cross-validate", () => {
  it("reports no issues when every required field has a question and every maps_to hits the schema", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    expect(crossValidate(baseSchema, questions)).toEqual([]);
  });

  it("reports maps_to pointing to a path not in the schema", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
        { id: "q_ghost", section: "A", type: "text", text: "?", maps_to: "identity.ghost" },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    expect(issues).toHaveLength(1);
    expect(issues[0]?.kind).toBe("maps_to-unknown-path");
    expect(issues[0]?.where).toBe("q_ghost");
  });

  it("reports required field without a matching question or default", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    expect(issues.some((i) => i.kind === "required-uncovered" && i.where === "identity.name")).toBe(true);
  });

  it("does not report required field if it has a default", () => {
    const schema = parseSchemaFile({
      version: "0.1.0",
      sections: [
        {
          id: "A",
          name: "x",
          fields: [{ path: "identity.license", type: "enum", values: ["MIT"], required: true, default: "MIT" }],
        },
      ],
    });
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [{ id: "q_intro", section: "A", type: "info", text: "hi" }],
    });
    expect(crossValidate(schema, questions)).toEqual([]);
  });

  it("reports question referencing a section id not present in schema", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
        { id: "q_orphan", section: "G", type: "text", text: "?", maps_to: "identity.license" },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    expect(issues.some((i) => i.kind === "section-unknown" && i.where === "q_orphan")).toBe(true);
  });

  it("reports question-field-type-mismatch when question type doesn't match field type", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name_wrong", section: "A", type: "number", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    const mismatch = issues.find((i) => i.kind === "question-field-type-mismatch");
    expect(mismatch?.where).toBe("q_name_wrong");
    expect(mismatch?.detail).toMatch(/'number' expects field type 'number' but 'identity\.name' is 'string'/);
  });

  it("reports question-section-mismatch when question sits in a different section than its field", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language_wrong_section",
          section: "A",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    const mismatch = issues.find((i) => i.kind === "question-section-mismatch");
    expect(mismatch?.where).toBe("q_language_wrong_section");
    expect(mismatch?.detail).toMatch(/section 'A'.*field 'stack\.language' lives in section 'C'/);
  });

  it("reports when-unknown-path when a when expression references a missing path", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          when: "stack.langage == 'python'",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    const unknown = issues.find((i) => i.kind === "when-unknown-path");
    expect(unknown?.where).toBe("q_language");
    expect(unknown?.detail).toMatch(/'stack\.langage'/);
  });

  it("accepts when expressions that only reference existing schema paths", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          when: "stack.language in ['typescript', 'python']",
          options: [{ value: "typescript" }, { value: "python" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    expect(issues.filter((i) => i.kind === "when-unknown-path")).toEqual([]);
  });

  it("reports option value outside enum values for single/multi", () => {
    const questions = parseQuestionsFile({
      version: "0.1.0",
      questions: [
        { id: "q_name", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        {
          id: "q_language",
          section: "C",
          type: "single",
          text: "?",
          maps_to: "stack.language",
          options: [{ value: "typescript" }, { value: "ruby" }],
        },
      ],
    });
    const issues = crossValidate(baseSchema, questions);
    expect(
      issues.some(
        (i) => i.kind === "option-outside-enum" && i.where === "q_language" && i.detail.includes("ruby")
      )
    ).toBe(true);
  });
});
