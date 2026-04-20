import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("AGENTS.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "AGENTS.md", content: template(profile) },
];
