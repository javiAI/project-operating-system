import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const configTemplate = loadTemplate("vault/config.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => {
  const answers = profile.answers as Record<string, unknown>;
  const integrations = (answers.integrations ?? {}) as Record<string, unknown>;
  const kp = (integrations.knowledge_plane ?? {}) as Record<string, unknown>;

  if (kp.enabled !== true) {
    return [];
  }

  return [
    { path: "vault/config.md", content: configTemplate(profile) },
    { path: "vault/raw/.gitkeep", content: "\n" },
    { path: "vault/wiki/.gitkeep", content: "\n" },
  ];
};
