import type Handlebars from "handlebars";

type HandlebarsInstance = typeof Handlebars;

export function registerHelpers(hb: HandlebarsInstance): void {
  hb.registerHelper("eq", (a: unknown, b: unknown) => a === b);
  hb.registerHelper("neq", (a: unknown, b: unknown) => a !== b);
  hb.registerHelper(
    "includes",
    (collection: unknown, value: unknown) =>
      Array.isArray(collection) && collection.includes(value)
  );
  hb.registerHelper("kebabCase", (value: unknown) =>
    typeof value === "string" ? kebabCase(value) : ""
  );
  hb.registerHelper("upperFirst", (value: unknown) =>
    typeof value === "string" && value.length > 0
      ? value.charAt(0).toUpperCase() + value.slice(1)
      : ""
  );
  hb.registerHelper("jsonStringify", (value: unknown) => JSON.stringify(value, null, 2));
}

function kebabCase(input: string): string {
  return input
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/[_\s]+/g, "-")
    .replace(/-+/g, "-")
    .toLowerCase();
}
