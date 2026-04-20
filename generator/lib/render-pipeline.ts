import { mkdir, readdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";

export { type Profile } from "./profile-model.ts";
import type { Profile } from "./profile-model.ts";

export type FileWrite = {
  path: string;
  content: string;
};

export type Renderer = (profile: Profile) => FileWrite[];

export function renderAll(profile: Profile, renderers: Renderer[]): FileWrite[] {
  const all: FileWrite[] = [];
  const seen = new Map<string, number>();
  for (const [i, renderer] of renderers.entries()) {
    const out = renderer(profile);
    for (const file of out) {
      const prev = seen.get(file.path);
      if (prev !== undefined) {
        throw new Error(
          `render-pipeline: path collision '${file.path}' emitted by renderer[${prev}] and renderer[${i}]`
        );
      }
      seen.set(file.path, i);
      all.push(file);
    }
  }
  return all;
}

export async function writeFiles(outDir: string, files: FileWrite[]): Promise<void> {
  const resolvedOut = path.resolve(outDir);
  await mkdir(resolvedOut, { recursive: true });
  for (const file of files) {
    if (path.isAbsolute(file.path)) {
      throw new Error(
        `render-pipeline/writeFiles: absolute path rejected: '${file.path}'`
      );
    }
    const abs = path.resolve(resolvedOut, file.path);
    const relative = path.relative(resolvedOut, abs);
    if (
      relative === ".." ||
      relative.startsWith(`..${path.sep}`) ||
      path.isAbsolute(relative)
    ) {
      throw new Error(
        `render-pipeline/writeFiles: path escapes outDir: '${file.path}'`
      );
    }
    await mkdir(path.dirname(abs), { recursive: true });
    await writeFile(abs, file.content, "utf8");
  }
}

export async function isDirEmpty(dir: string): Promise<boolean> {
  try {
    const s = await stat(dir);
    if (!s.isDirectory()) return false;
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return true;
    throw err;
  }
  const entries = await readdir(dir);
  return entries.length === 0;
}
