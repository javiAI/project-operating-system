import { describe, expect, it } from "vitest";
import { evaluateCondition, parseCondition } from "./condition-parser.ts";

describe("condition-parser / parse", () => {
  it("parses equality with string literal", () => {
    const ast = parseCondition("stack.language == 'python'");
    expect(ast.kind).toBe("compare");
  });

  it("parses inequality", () => {
    const ast = parseCondition("stack.language != 'go'");
    expect(ast.kind).toBe("compare");
  });

  it("parses 'in' membership with array literal", () => {
    const ast = parseCondition("stack.language in ['typescript', 'javascript']");
    expect(ast.kind).toBe("compare");
  });

  it("parses and/or with parens", () => {
    const ast = parseCondition(
      "(stack.language == 'python' || stack.language == 'typescript') && testing.coverage_threshold == 80"
    );
    expect(ast.kind).toBe("and");
  });

  it("parses boolean literal", () => {
    const ast = parseCondition("claude_code.solo == true");
    expect(ast.kind).toBe("compare");
  });

  it("parses number literal", () => {
    const ast = parseCondition("testing.coverage_threshold == 80");
    expect(ast.kind).toBe("compare");
  });

  it("rejects unterminated string", () => {
    expect(() => parseCondition("x == 'abc")).toThrow(/unterminated string/i);
  });

  it("rejects trailing garbage", () => {
    expect(() => parseCondition("x == 'y' garbage")).toThrow(/unexpected/i);
  });

  it("rejects unknown operator", () => {
    expect(() => parseCondition("x ~= 'y'")).toThrow();
  });

  it("rejects empty input", () => {
    expect(() => parseCondition("")).toThrow(/empty/i);
  });

  it("rejects array element that is not a literal", () => {
    expect(() => parseCondition("x in [y, 'z']")).toThrow(/literal/i);
  });

  it("rejects unterminated array literal", () => {
    expect(() => parseCondition("x in ['y', 'z'")).toThrow();
  });

  it("parses empty array literal", () => {
    const ast = parseCondition("x in []");
    expect(ast.kind).toBe("compare");
  });

  it("parses not operator on a parenthesized comparison", () => {
    const ast = parseCondition("!(x == 'y')");
    expect(ast.kind).toBe("not");
  });
});

describe("condition-parser / evaluate", () => {
  const ctx = {
    stack: { language: "python", version: "3.12" },
    testing: { coverage_threshold: 80 },
    claude_code: { solo: true },
  };

  it("evaluates equality true", () => {
    expect(evaluateCondition(parseCondition("stack.language == 'python'"), ctx)).toBe(true);
  });

  it("evaluates equality false", () => {
    expect(evaluateCondition(parseCondition("stack.language == 'go'"), ctx)).toBe(false);
  });

  it("evaluates inequality", () => {
    expect(evaluateCondition(parseCondition("stack.language != 'go'"), ctx)).toBe(true);
  });

  it("evaluates 'in' membership", () => {
    expect(
      evaluateCondition(parseCondition("stack.language in ['python', 'ruby']"), ctx)
    ).toBe(true);
    expect(
      evaluateCondition(parseCondition("stack.language in ['go', 'rust']"), ctx)
    ).toBe(false);
  });

  it("evaluates && short-circuit", () => {
    expect(
      evaluateCondition(
        parseCondition("stack.language == 'python' && testing.coverage_threshold == 80"),
        ctx
      )
    ).toBe(true);
    expect(
      evaluateCondition(
        parseCondition("stack.language == 'go' && testing.coverage_threshold == 80"),
        ctx
      )
    ).toBe(false);
  });

  it("evaluates ||", () => {
    expect(
      evaluateCondition(
        parseCondition("stack.language == 'go' || stack.language == 'python'"),
        ctx
      )
    ).toBe(true);
  });

  it("evaluates nested parens", () => {
    expect(
      evaluateCondition(
        parseCondition(
          "(stack.language == 'python' || stack.language == 'ruby') && claude_code.solo == true"
        ),
        ctx
      )
    ).toBe(true);
  });

  it("returns false when path is missing", () => {
    expect(evaluateCondition(parseCondition("nonexistent.path == 'x'"), ctx)).toBe(false);
  });

  it("evaluates boolean literal", () => {
    expect(evaluateCondition(parseCondition("claude_code.solo == true"), ctx)).toBe(true);
  });

  it("evaluates number literal", () => {
    expect(
      evaluateCondition(parseCondition("testing.coverage_threshold == 80"), ctx)
    ).toBe(true);
  });

  it("evaluates not operator", () => {
    expect(
      evaluateCondition(parseCondition("!(stack.language == 'go')"), ctx)
    ).toBe(true);
  });

  it("evaluates 'in' returning false when right side is not an array", () => {
    expect(evaluateCondition(parseCondition("'x' in 'y'"), ctx)).toBe(false);
  });
});
