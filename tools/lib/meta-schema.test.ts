import { describe, expect, it } from "vitest";
import { parseQuestionsFile, parseSchemaFile } from "./meta-schema.ts";

const validSchema = {
  version: "0.1.0",
  sections: [
    {
      id: "A",
      name: "Identidad",
      fields: [
        { path: "identity.name", type: "string", required: true, pattern: "^[a-z][a-z0-9-]{2,}$" },
        { path: "identity.license", type: "enum", values: ["MIT", "Apache-2.0"], default: "MIT" },
      ],
    },
    {
      id: "C",
      name: "Stack",
      fields: [
        { path: "stack.language", type: "enum", values: ["typescript", "python"], required: true },
        { path: "stack.coverage_threshold", type: "number", default: 80, min: 0, max: 100 },
      ],
    },
  ],
};

const validQuestions = {
  version: "0.1.0",
  questions: [
    {
      id: "q_identity_name",
      section: "A",
      type: "text",
      text: "Nombre del proyecto",
      maps_to: "identity.name",
    },
    {
      id: "q_stack_language",
      section: "C",
      type: "single",
      text: "Lenguaje principal",
      options: [
        { value: "typescript", label: "TypeScript" },
        { value: "python", label: "Python" },
      ],
      maps_to: "stack.language",
    },
  ],
};

describe("meta-schema / schema.yaml", () => {
  it("accepts a valid schema", () => {
    expect(() => parseSchemaFile(validSchema)).not.toThrow();
  });

  it("rejects missing version", () => {
    const bad = { ...validSchema, version: undefined };
    expect(() => parseSchemaFile(bad)).toThrow();
  });

  it("rejects empty sections", () => {
    expect(() => parseSchemaFile({ ...validSchema, sections: [] })).toThrow();
  });

  it("rejects field with unknown type", () => {
    const bad = {
      ...validSchema,
      sections: [
        {
          id: "A",
          name: "x",
          fields: [{ path: "identity.name", type: "banana", required: true }],
        },
      ],
    };
    expect(() => parseSchemaFile(bad)).toThrow(/type/i);
  });

  it("rejects enum field without values", () => {
    const bad = {
      ...validSchema,
      sections: [
        {
          id: "A",
          name: "x",
          fields: [{ path: "identity.license", type: "enum", required: true }],
        },
      ],
    };
    expect(() => parseSchemaFile(bad)).toThrow(/values/i);
  });

  it("rejects enum default not in values", () => {
    const bad = {
      ...validSchema,
      sections: [
        {
          id: "A",
          name: "x",
          fields: [
            { path: "identity.license", type: "enum", values: ["MIT"], default: "GPL" },
          ],
        },
      ],
    };
    expect(() => parseSchemaFile(bad)).toThrow(/default/i);
  });

  it("rejects duplicate field paths", () => {
    const bad = {
      ...validSchema,
      sections: [
        {
          id: "A",
          name: "x",
          fields: [
            { path: "identity.name", type: "string", required: true },
            { path: "identity.name", type: "string", required: false },
          ],
        },
      ],
    };
    expect(() => parseSchemaFile(bad)).toThrow(/duplicate/i);
  });

  it("rejects field with invalid path format", () => {
    const bad = {
      ...validSchema,
      sections: [
        {
          id: "A",
          name: "x",
          fields: [{ path: "Invalid.Path!", type: "string", required: true }],
        },
      ],
    };
    expect(() => parseSchemaFile(bad)).toThrow(/path/i);
  });
});

describe("meta-schema / questions.yaml", () => {
  it("accepts valid questions", () => {
    expect(() => parseQuestionsFile(validQuestions)).not.toThrow();
  });

  it("rejects question without maps_to when type is text/single/multi", () => {
    const bad = {
      version: "0.1.0",
      questions: [
        { id: "q1", section: "A", type: "text", text: "?" },
      ],
    };
    expect(() => parseQuestionsFile(bad)).toThrow(/maps_to/i);
  });

  it("rejects single question with empty options", () => {
    const bad = {
      version: "0.1.0",
      questions: [
        { id: "q1", section: "A", type: "single", text: "?", maps_to: "x.y", options: [] },
      ],
    };
    expect(() => parseQuestionsFile(bad)).toThrow(/options/i);
  });

  it("rejects duplicate question ids", () => {
    const bad = {
      version: "0.1.0",
      questions: [
        { id: "q1", section: "A", type: "text", text: "?", maps_to: "identity.name" },
        { id: "q1", section: "A", type: "text", text: "?", maps_to: "identity.description" },
      ],
    };
    expect(() => parseQuestionsFile(bad)).toThrow(/duplicate/i);
  });

  it("rejects invalid condition DSL in 'when'", () => {
    const bad = {
      version: "0.1.0",
      questions: [
        {
          id: "q1",
          section: "C",
          type: "text",
          text: "?",
          maps_to: "stack.x",
          when: "stack.language ~~ 'python'",
        },
      ],
    };
    expect(() => parseQuestionsFile(bad)).toThrow(/when/i);
  });

  it("accepts question type 'info' without maps_to", () => {
    const ok = {
      version: "0.1.0",
      questions: [
        { id: "intro", section: "A", type: "info", text: "Welcome" },
      ],
    };
    expect(() => parseQuestionsFile(ok)).not.toThrow();
  });

  it("accepts multi question with options + maps_to", () => {
    const ok = {
      version: "0.1.0",
      questions: [
        {
          id: "q1",
          section: "E",
          type: "multi",
          text: "Select MCPs",
          options: [{ value: "mempalace" }, { value: "notebooklm" }],
          maps_to: "integrations.mcps",
        },
      ],
    };
    expect(() => parseQuestionsFile(ok)).not.toThrow();
  });
});
