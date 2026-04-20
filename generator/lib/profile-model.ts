import type { ProfileFile } from "./schema.ts";

export const USER_SPECIFIC_PATHS = [
  "identity.name",
  "identity.description",
  "identity.owner",
] as const;

export type UserSpecificPath = (typeof USER_SPECIFIC_PATHS)[number];

export type Profile = {
  meta: {
    version: string;
    profileName: string;
    profileDescription: string;
  };
  answers: Record<string, unknown>;
  placeholders: readonly string[];
};

export function buildProfile(input: ProfileFile): Profile {
  const answers: Record<string, unknown> = {};
  for (const [path, value] of Object.entries(input.answers)) {
    setNested(answers, path, value);
  }

  const placeholders: string[] = [];
  for (const path of USER_SPECIFIC_PATHS) {
    if (getNested(answers, path) === undefined) {
      setNested(answers, path, `TODO(${path})`);
      placeholders.push(path);
    }
  }

  return {
    meta: {
      version: input.version,
      profileName: input.profile.name,
      profileDescription: input.profile.description,
    },
    answers,
    placeholders,
  };
}

function setNested(root: Record<string, unknown>, dotted: string, value: unknown): void {
  const parts = dotted.split(".");
  let cursor: Record<string, unknown> = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i];
    const existing = cursor[key];
    if (existing === undefined) {
      const child: Record<string, unknown> = {};
      cursor[key] = child;
      cursor = child;
      continue;
    }
    if (!isPlainObject(existing)) {
      throw new Error(
        `collision at '${parts.slice(0, i + 1).join(".")}': leaf value conflicts with nested path '${dotted}'`
      );
    }
    cursor = existing;
  }
  const leafKey = parts[parts.length - 1];
  const existingLeaf = cursor[leafKey];
  if (existingLeaf !== undefined && isPlainObject(existingLeaf)) {
    throw new Error(
      `collision at '${dotted}': nested object conflicts with leaf assignment`
    );
  }
  cursor[leafKey] = value;
}

function getNested(root: Record<string, unknown>, dotted: string): unknown {
  const parts = dotted.split(".");
  let cursor: unknown = root;
  for (const part of parts) {
    if (!isPlainObject(cursor)) return undefined;
    cursor = (cursor as Record<string, unknown>)[part];
  }
  return cursor;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
