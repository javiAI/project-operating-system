import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("MASTER_PLAN.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "MASTER_PLAN.md", content: template(profile) },
];
