import { describe, expect, it } from "vitest";
import Handlebars from "handlebars";
import { registerHelpers } from "./handlebars-helpers.ts";

function compile(src: string): (ctx: unknown) => string {
  const hb = Handlebars.create();
  registerHelpers(hb);
  return hb.compile(src, { noEscape: true });
}

describe("registerHelpers — eq / neq", () => {
  it("eq returns true for equal primitive operands", () => {
    expect(compile("{{#if (eq x 'foo')}}yes{{else}}no{{/if}}")({ x: "foo" })).toBe("yes");
    expect(compile("{{#if (eq n 5)}}yes{{else}}no{{/if}}")({ n: 5 })).toBe("yes");
    expect(compile("{{#if (eq b true)}}yes{{else}}no{{/if}}")({ b: true })).toBe("yes");
  });

  it("eq returns false for unequal operands", () => {
    expect(compile("{{#if (eq x 'foo')}}yes{{else}}no{{/if}}")({ x: "bar" })).toBe("no");
  });

  it("neq is the inverse of eq", () => {
    expect(compile("{{#if (neq x 'foo')}}yes{{else}}no{{/if}}")({ x: "bar" })).toBe("yes");
    expect(compile("{{#if (neq x 'foo')}}yes{{else}}no{{/if}}")({ x: "foo" })).toBe("no");
  });
});

describe("registerHelpers — includes", () => {
  it("returns true when the array contains the value", () => {
    expect(
      compile("{{#if (includes providers 'github')}}yes{{else}}no{{/if}}")({
        providers: ["github", "gitlab"],
      })
    ).toBe("yes");
  });

  it("returns false when the array does not contain the value", () => {
    expect(
      compile("{{#if (includes providers 'bitbucket')}}yes{{else}}no{{/if}}")({
        providers: ["github", "gitlab"],
      })
    ).toBe("no");
  });

  it("returns false when the first argument is not an array", () => {
    expect(
      compile("{{#if (includes providers 'x')}}yes{{else}}no{{/if}}")({ providers: "github" })
    ).toBe("no");
    expect(
      compile("{{#if (includes providers 'x')}}yes{{else}}no{{/if}}")({ providers: undefined })
    ).toBe("no");
  });
});

describe("registerHelpers — kebabCase", () => {
  it("converts camelCase to kebab-case", () => {
    expect(compile("{{kebabCase name}}")({ name: "myAwesomeProject" })).toBe("my-awesome-project");
  });

  it("converts snake_case to kebab-case", () => {
    expect(compile("{{kebabCase name}}")({ name: "my_awesome_project" })).toBe(
      "my-awesome-project"
    );
  });

  it("lowercases already-kebab strings", () => {
    expect(compile("{{kebabCase name}}")({ name: "Already-Kebab" })).toBe("already-kebab");
  });

  it("collapses whitespace runs into single dashes", () => {
    expect(compile("{{kebabCase name}}")({ name: "hello  world" })).toBe("hello-world");
  });

  it("returns empty string for non-string input", () => {
    expect(compile("{{kebabCase name}}")({ name: undefined })).toBe("");
    expect(compile("{{kebabCase name}}")({ name: 42 })).toBe("");
  });
});

describe("registerHelpers — upperFirst", () => {
  it("capitalizes the first character and preserves the rest", () => {
    expect(compile("{{upperFirst name}}")({ name: "foo" })).toBe("Foo");
    expect(compile("{{upperFirst name}}")({ name: "foo bar" })).toBe("Foo bar");
  });

  it("is a no-op when the first character is already uppercase", () => {
    expect(compile("{{upperFirst name}}")({ name: "Foo" })).toBe("Foo");
  });

  it("returns empty string for non-string input", () => {
    expect(compile("{{upperFirst name}}")({ name: undefined })).toBe("");
  });

  it("returns empty string for empty input", () => {
    expect(compile("{{upperFirst name}}")({ name: "" })).toBe("");
  });
});

describe("registerHelpers — jsonStringify", () => {
  it("stringifies an object with 2-space indent", () => {
    expect(compile("{{jsonStringify obj}}")({ obj: { a: 1, b: "x" } })).toBe(
      '{\n  "a": 1,\n  "b": "x"\n}'
    );
  });

  it("is deterministic: same input produces same output", () => {
    const template = compile("{{jsonStringify obj}}");
    const ctx = { obj: { foo: [1, 2, 3], bar: { nested: true } } };
    expect(template(ctx)).toBe(template(ctx));
  });

  it("handles arrays and primitives", () => {
    expect(compile("{{jsonStringify arr}}")({ arr: [1, 2, 3] })).toBe("[\n  1,\n  2,\n  3\n]");
    expect(compile("{{jsonStringify n}}")({ n: 42 })).toBe("42");
  });
});

describe("registerHelpers — idempotence", () => {
  it("registering twice does not throw and yields consistent output", () => {
    const hb = Handlebars.create();
    registerHelpers(hb);
    registerHelpers(hb);
    const out = hb.compile("{{upperFirst x}}")({ x: "hi" });
    expect(out).toBe("Hi");
  });
});
