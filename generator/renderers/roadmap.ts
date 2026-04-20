import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("ROADMAP.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "ROADMAP.md", content: template(profile) },
];
