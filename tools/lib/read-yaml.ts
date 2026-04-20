import { readFile } from "node:fs/promises";
import { parse as parseYaml } from "yaml";

export type ReadResult = { ok: true; value: unknown } | { ok: false; error: string };

export async function readAndParseYaml(path: string): Promise<ReadResult> {
  let raw: string;
  try {
    raw = await readFile(path, "utf8");
  } catch (err) {
    return { ok: false, error: `cannot read ${path}: ${errorMessage(err)}` };
  }
  try {
    return { ok: true, value: parseYaml(raw) };
  } catch (err) {
    return { ok: false, error: `cannot parse ${path}: ${errorMessage(err)}` };
  }
}

export function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}
