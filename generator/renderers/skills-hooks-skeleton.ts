import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const settingsTemplate = loadTemplate(".claude/settings.json.hbs");
const hooksReadmeTemplate = loadTemplate(".claude/hooks/README.md.hbs");
const skillsReadmeTemplate = loadTemplate(".claude/skills/README.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => {
  return [
    { path: ".claude/settings.json", content: settingsTemplate(profile) },
    { path: ".claude/hooks/README.md", content: hooksReadmeTemplate(profile) },
    { path: ".claude/skills/README.md", content: skillsReadmeTemplate(profile) },
  ];
};
