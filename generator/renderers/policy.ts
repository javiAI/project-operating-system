import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const template = loadTemplate("policy.yaml.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: "policy.yaml", content: template(profile) },
];
