import Handlebars from "handlebars";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { registerHelpers } from "./handlebars-helpers.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
export const TEMPLATES_DIR = path.resolve(here, "../../templates");

export type CompiledTemplate = (context: unknown) => string;

export function loadTemplate(relativePath: string): CompiledTemplate {
  const absolute = path.join(TEMPLATES_DIR, relativePath);
  const source = readFileSync(absolute, "utf8");
  const hb = Handlebars.create();
  registerHelpers(hb);
  return hb.compile(source, { noEscape: true });
}
