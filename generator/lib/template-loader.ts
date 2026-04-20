import Handlebars from "handlebars";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { registerHelpers } from "./handlebars-helpers.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
export const TEMPLATES_DIR = path.resolve(here, "../../templates");

export type CompiledTemplate = (context: unknown) => string;

export function loadTemplate(relativePath: string): CompiledTemplate {
  if (path.isAbsolute(relativePath)) {
    throw new Error(
      `template-loader/loadTemplate: absolute path rejected: '${relativePath}'`
    );
  }
  const absolute = path.resolve(TEMPLATES_DIR, relativePath);
  const relative = path.relative(TEMPLATES_DIR, absolute);
  if (
    relative === ".." ||
    relative.startsWith(`..${path.sep}`) ||
    path.isAbsolute(relative)
  ) {
    throw new Error(
      `template-loader/loadTemplate: path escapes templates dir: '${relativePath}'`
    );
  }
  const source = readFileSync(absolute, "utf8");
  const hb = Handlebars.create();
  registerHelpers(hb);
  return hb.compile(source, { noEscape: true });
}
