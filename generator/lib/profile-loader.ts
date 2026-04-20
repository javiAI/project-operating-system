import { errorMessage, readAndParseYaml } from "../../tools/lib/read-yaml.ts";
import { parseProfileFile, type ProfileFile } from "./schema.ts";

export type LoadResult =
  | { ok: true; profile: ProfileFile }
  | { ok: false; error: string };

export async function loadProfile(path: string): Promise<LoadResult> {
  const read = await readAndParseYaml(path);
  if (!read.ok) {
    return { ok: false, error: read.error };
  }
  try {
    return { ok: true, profile: parseProfileFile(read.value) };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}
