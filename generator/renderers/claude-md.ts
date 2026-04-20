import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("CLAUDE.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "CLAUDE.md", content: template(profile) },
];
