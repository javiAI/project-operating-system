import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const readmeTemplate = loadTemplate("tests/README.md.hbs");
const smokeTsTemplate = loadTemplate("tests/smoke.test.ts.hbs");
const smokePyTemplate = loadTemplate("tests/test_smoke.py.hbs");
const vitestConfigTemplate = loadTemplate("vitest.config.ts.hbs");
const pytestIniTemplate = loadTemplate("pytest.ini.hbs");
const makefileTemplate = loadTemplate("Makefile.hbs");

const DEFERRED_FRAMEWORKS = new Set(["jest", "go-test", "cargo-test"]);

export const render: Renderer = (profile: Profile): FileWrite[] => {
  const answers = profile.answers as Record<string, unknown>;
  const stack = (answers.stack ?? {}) as Record<string, unknown>;
  const testing = (answers.testing ?? {}) as Record<string, unknown>;
  const language = stack.language;
  const framework = testing.unit_framework;

  if (typeof framework === "string" && DEFERRED_FRAMEWORKS.has(framework)) {
    throw new Error(
      `renderers/tests: framework '${framework}' declared at ` +
        `testing.unit_framework is deferred in C3 — no template emitted until ` +
        `a canonical profile adopts it (CLAUDE.md #7: patterns before abstraction).`
    );
  }

  if (language === "typescript" && framework === "vitest") {
    return [
      { path: "tests/README.md", content: readmeTemplate(profile) },
      { path: "tests/smoke.test.ts", content: smokeTsTemplate(profile) },
      { path: "vitest.config.ts", content: vitestConfigTemplate(profile) },
      { path: "Makefile", content: makefileTemplate(profile) },
    ];
  }

  if (language === "python" && framework === "pytest") {
    return [
      { path: "tests/README.md", content: readmeTemplate(profile) },
      { path: "tests/test_smoke.py", content: smokePyTemplate(profile) },
      { path: "pytest.ini", content: pytestIniTemplate(profile) },
      { path: "Makefile", content: makefileTemplate(profile) },
    ];
  }

  throw new Error(
    `renderers/tests: unsupported combination at ` +
      `stack.language='${String(language)}' + testing.unit_framework='${String(framework)}'. ` +
      `C3 supports typescript+vitest and python+pytest only.`
  );
};
