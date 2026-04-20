import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { parseProfileFile } from "../lib/schema.ts";
import { buildProfile, type Profile } from "../lib/profile-model.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const PROFILES_DIR = path.resolve(here, "../../questionnaire/profiles");

export type CanonicalProfile = {
  slug: string;
  profile: Profile;
};

export const CANONICAL_SLUGS = ["nextjs-app", "agent-sdk", "cli-tool"] as const;

export function loadCanonicalProfiles(): CanonicalProfile[] {
  return CANONICAL_SLUGS.map((slug) => {
    const raw = readFileSync(path.join(PROFILES_DIR, `${slug}.yaml`), "utf8");
    const parsed = parseProfileFile(parseYaml(raw));
    return { slug, profile: buildProfile(parsed) };
  });
}
