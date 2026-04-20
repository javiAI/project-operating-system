import { describe, expect, it } from "vitest";
import { parseSchemaFile } from "../../tools/lib/meta-schema.ts";
import { parseProfileFile } from "../../tools/lib/profile-validator.ts";
import { readAndParseYaml } from "../../tools/lib/read-yaml.ts";
import { completenessCheck, USER_SPECIFIC_PATHS } from "./validators.ts";

const SCHEMA_PATH = "questionnaire/schema.yaml";

async function loadSchema() {
  const r = await readAndParseYaml(SCHEMA_PATH);
  if (!r.ok) throw new Error(r.error);
  return parseSchemaFile(r.value);
}

function profile(answers: Record<string, unknown>) {
  return parseProfileFile({
    version: "0.1.0",
    profile: { name: "t", description: "t" },
    answers,
  });
}

describe("completenessCheck", () => {
  it("emits 3 warnings and 0 errors when only user-specific required paths are missing", async () => {
    const schema = await loadSchema();
    const p = profile({
      "domain.type": "web-app",
      "stack.language": "typescript",
      "testing.unit_framework": "vitest",
    });
    const result = completenessCheck(schema, p);
    expect(result.errors).toHaveLength(0);
    expect(result.warnings).toHaveLength(3);
    const warningPaths = result.warnings.map((w) => w.path).sort();
    expect(warningPaths).toEqual([...USER_SPECIFIC_PATHS].sort());
  });

  it("emits 0 warnings and 0 errors when every required path is present", async () => {
    const schema = await loadSchema();
    const p = profile({
      "identity.name": "x",
      "identity.description": "y",
      "identity.owner": "z",
      "domain.type": "web-app",
      "stack.language": "typescript",
      "testing.unit_framework": "vitest",
    });
    const result = completenessCheck(schema, p);
    expect(result.errors).toHaveLength(0);
    expect(result.warnings).toHaveLength(0);
  });

  it("emits 1 error when a non-user-specific required (domain.type) is missing", async () => {
    const schema = await loadSchema();
    const p = profile({
      "stack.language": "typescript",
      "testing.unit_framework": "vitest",
    });
    const result = completenessCheck(schema, p);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]?.path).toBe("domain.type");
    expect(result.warnings).toHaveLength(3);
  });

  it("emits 2 errors when two non-user-specific required fields are missing", async () => {
    const schema = await loadSchema();
    const p = profile({
      "testing.unit_framework": "vitest",
    });
    const result = completenessCheck(schema, p);
    expect(result.errors).toHaveLength(2);
    const errorPaths = result.errors.map((e) => e.path).sort();
    expect(errorPaths).toEqual(["domain.type", "stack.language"]);
  });

  it("treats a required field with a declared default as satisfied even if not in profile", async () => {
    const syntheticSchema = parseSchemaFile({
      version: "0.1.0",
      sections: [
        {
          id: "A",
          name: "A",
          fields: [
            { path: "a.req_no_default", type: "string", required: true },
            { path: "a.req_with_default", type: "string", required: true, default: "d" },
          ],
        },
      ],
    });
    const p = profile({});
    const result = completenessCheck(syntheticSchema, p);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]?.path).toBe("a.req_no_default");
    expect(result.warnings).toHaveLength(0);
  });
});
