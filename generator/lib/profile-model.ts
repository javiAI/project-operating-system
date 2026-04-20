import type { ProfileFile } from "./schema.ts";
import { USER_SPECIFIC_PATHS } from "./validators.ts";

export { USER_SPECIFIC_PATHS };

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
  const leafKey = parts.pop();
  if (leafKey === undefined || leafKey === "") {
    throw new Error(`invalid dotted path: '${dotted}'`);
  }

  let cursor: Record<string, unknown> = root;
  const walked: string[] = [];
  for (const key of parts) {
    if (key === "") {
      throw new Error(`invalid dotted path: '${dotted}'`);
    }
    walked.push(key);
    const existing = cursor[key];
    if (existing === undefined) {
      const child: Record<string, unknown> = {};
      cursor[key] = child;
      cursor = child;
      continue;
    }
    if (!isPlainObject(existing)) {
      throw new Error(
        `collision at '${walked.join(".")}': leaf value conflicts with nested path '${dotted}'`
      );
    }
    cursor = existing;
  }

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
