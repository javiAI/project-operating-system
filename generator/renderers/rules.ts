import { loadTemplate } from "../lib/template-loader.ts";
import type { FileWrite, Profile, Renderer } from "../lib/render-pipeline.ts";

const docsTemplate = loadTemplate(".claude/rules/docs.md.hbs");
const patternsTemplate = loadTemplate(".claude/rules/patterns.md.hbs");

export const render: Renderer = (profile: Profile): FileWrite[] => [
  { path: ".claude/rules/docs.md", content: docsTemplate(profile) },
  { path: ".claude/rules/patterns.md", content: patternsTemplate(profile) },
];
