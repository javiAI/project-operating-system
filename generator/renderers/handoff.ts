import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("HANDOFF.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "HANDOFF.md", content: template(profile) },
];
