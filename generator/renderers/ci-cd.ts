import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const ciYmlTemplate = loadTemplate(".github/workflows/ci.yml.hbs");
const branchProtectionTemplate = loadTemplate("docs/BRANCH_PROTECTION.md.hbs");

const DEFERRED_CI_HOSTS = new Set(["gitlab", "bitbucket"]);

export const render: Renderer = (profile: Profile): FileWrite[] => {
  const answers = profile.answers as Record<string, unknown>;
  const workflow = (answers.workflow ?? {}) as Record<string, unknown>;
  const ciHost = workflow.ci_host;
  const branchProtection = workflow.branch_protection;

  if (typeof ciHost === "string" && DEFERRED_CI_HOSTS.has(ciHost)) {
    throw new Error(
      `renderers/ci-cd: ci_host '${ciHost}' declared at workflow.ci_host ` +
        `is deferred in C4 — no template emitted until a canonical profile adopts it ` +
        `(CLAUDE.md #7: patterns before abstraction).`
    );
  }

  if (ciHost !== "github") {
    throw new Error(
      `renderers/ci-cd: unsupported workflow.ci_host='${String(ciHost)}'. ` +
        `C4 supports 'github' only.`
    );
  }

  const files: FileWrite[] = [
    { path: ".github/workflows/ci.yml", content: ciYmlTemplate(profile) },
  ];

  if (branchProtection === true) {
    files.push({
      path: "docs/BRANCH_PROTECTION.md",
      content: branchProtectionTemplate(profile),
    });
  }

  return files;
};
