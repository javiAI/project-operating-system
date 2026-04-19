export type Literal = string | number | boolean | null;

export type ConditionAst =
  | { kind: "and"; left: ConditionAst; right: ConditionAst }
  | { kind: "or"; left: ConditionAst; right: ConditionAst }
  | { kind: "not"; expr: ConditionAst }
  | { kind: "compare"; op: "==" | "!=" | "in"; left: Operand; right: Operand };

export type Operand =
  | { kind: "path"; segments: string[] }
  | { kind: "literal"; value: Literal }
  | { kind: "array"; values: Literal[] };

type Token =
  | { type: "ident"; value: string }
  | { type: "string"; value: string }
  | { type: "number"; value: number }
  | { type: "bool"; value: boolean }
  | { type: "null" }
  | { type: "op"; value: "==" | "!=" | "&&" | "||" | "!" | "(" | ")" | "[" | "]" | "," | "in" };

class Lexer {
  private pos = 0;
  constructor(private readonly src: string) {}

  private peek(offset = 0): string {
    return this.src[this.pos + offset] ?? "";
  }

  private advance(): string {
    const ch = this.src[this.pos] ?? "";
    this.pos++;
    return ch;
  }

  tokenize(): Token[] {
    const tokens: Token[] = [];
    while (this.pos < this.src.length) {
      const ch = this.peek();
      if (ch === " " || ch === "\t" || ch === "\n" || ch === "\r") {
        this.advance();
        continue;
      }
      if (ch === "'" || ch === '"') {
        tokens.push(this.readString(ch));
        continue;
      }
      if (ch >= "0" && ch <= "9") {
        tokens.push(this.readNumber());
        continue;
      }
      if (this.isIdentStart(ch)) {
        tokens.push(this.readIdentOrKeyword());
        continue;
      }
      if (ch === "=" && this.peek(1) === "=") {
        this.advance(); this.advance();
        tokens.push({ type: "op", value: "==" });
        continue;
      }
      if (ch === "!" && this.peek(1) === "=") {
        this.advance(); this.advance();
        tokens.push({ type: "op", value: "!=" });
        continue;
      }
      if (ch === "&" && this.peek(1) === "&") {
        this.advance(); this.advance();
        tokens.push({ type: "op", value: "&&" });
        continue;
      }
      if (ch === "|" && this.peek(1) === "|") {
        this.advance(); this.advance();
        tokens.push({ type: "op", value: "||" });
        continue;
      }
      if (ch === "!" || ch === "(" || ch === ")" || ch === "[" || ch === "]" || ch === ",") {
        this.advance();
        tokens.push({ type: "op", value: ch });
        continue;
      }
      throw new Error(`condition-parser: unexpected character '${ch}' at position ${this.pos}`);
    }
    return tokens;
  }

  private isIdentStart(ch: string): boolean {
    return (ch >= "a" && ch <= "z") || (ch >= "A" && ch <= "Z") || ch === "_";
  }

  private isIdentPart(ch: string): boolean {
    return this.isIdentStart(ch) || (ch >= "0" && ch <= "9") || ch === ".";
  }

  private readString(quote: string): Token {
    this.advance();
    let value = "";
    while (this.pos < this.src.length) {
      const ch = this.peek();
      if (ch === "\\" && this.peek(1) === quote) {
        this.advance(); this.advance();
        value += quote;
        continue;
      }
      if (ch === quote) {
        this.advance();
        return { type: "string", value };
      }
      value += this.advance();
    }
    throw new Error("condition-parser: unterminated string literal");
  }

  private readNumber(): Token {
    let raw = "";
    while (this.pos < this.src.length) {
      const ch = this.peek();
      if ((ch >= "0" && ch <= "9") || ch === ".") {
        raw += this.advance();
        continue;
      }
      break;
    }
    const n = Number(raw);
    if (Number.isNaN(n)) throw new Error(`condition-parser: invalid number '${raw}'`);
    return { type: "number", value: n };
  }

  private readIdentOrKeyword(): Token {
    let raw = "";
    while (this.pos < this.src.length && this.isIdentPart(this.peek())) {
      raw += this.advance();
    }
    if (raw === "true") return { type: "bool", value: true };
    if (raw === "false") return { type: "bool", value: false };
    if (raw === "null") return { type: "null" };
    if (raw === "in") return { type: "op", value: "in" };
    return { type: "ident", value: raw };
  }
}

class Parser {
  private pos = 0;
  constructor(private readonly tokens: Token[]) {}

  private peek(offset = 0): Token | undefined {
    return this.tokens[this.pos + offset];
  }

  private advance(): Token | undefined {
    const t = this.tokens[this.pos];
    this.pos++;
    return t;
  }

  private expect(pred: (t: Token | undefined) => boolean, msg: string): Token {
    const t = this.peek();
    if (!pred(t)) throw new Error(`condition-parser: ${msg} (got ${describe(t)})`);
    this.pos++;
    return t as Token;
  }

  parseRoot(): ConditionAst {
    if (this.tokens.length === 0) throw new Error("condition-parser: empty expression");
    const ast = this.parseOr();
    if (this.pos !== this.tokens.length) {
      throw new Error(`condition-parser: unexpected token ${describe(this.peek())}`);
    }
    return ast;
  }

  private parseOr(): ConditionAst {
    let left = this.parseAnd();
    while (this.matchOp("||")) {
      const right = this.parseAnd();
      left = { kind: "or", left, right };
    }
    return left;
  }

  private parseAnd(): ConditionAst {
    let left = this.parseNot();
    while (this.matchOp("&&")) {
      const right = this.parseNot();
      left = { kind: "and", left, right };
    }
    return left;
  }

  private parseNot(): ConditionAst {
    if (this.matchOp("!")) {
      const expr = this.parsePrimary();
      return { kind: "not", expr };
    }
    return this.parsePrimary();
  }

  private parsePrimary(): ConditionAst {
    if (this.matchOp("(")) {
      const ast = this.parseOr();
      this.expect((t) => t?.type === "op" && t.value === ")", "expected ')'");
      return ast;
    }
    return this.parseComparison();
  }

  private parseComparison(): ConditionAst {
    const left = this.parseOperand();
    const op = this.peek();
    if (!op || op.type !== "op" || (op.value !== "==" && op.value !== "!=" && op.value !== "in")) {
      throw new Error(`condition-parser: expected comparison operator (got ${describe(op)})`);
    }
    this.advance();
    const right = this.parseOperand();
    return { kind: "compare", op: op.value, left, right };
  }

  private parseOperand(): Operand {
    const t = this.peek();
    if (!t) throw new Error("condition-parser: unexpected end of input");
    if (t.type === "ident") {
      this.advance();
      return { kind: "path", segments: t.value.split(".") };
    }
    if (t.type === "string") {
      this.advance();
      return { kind: "literal", value: t.value };
    }
    if (t.type === "number") {
      this.advance();
      return { kind: "literal", value: t.value };
    }
    if (t.type === "bool") {
      this.advance();
      return { kind: "literal", value: t.value };
    }
    if (t.type === "null") {
      this.advance();
      return { kind: "literal", value: null };
    }
    if (t.type === "op" && t.value === "[") {
      this.advance();
      return this.parseArrayLiteral();
    }
    throw new Error(`condition-parser: expected operand (got ${describe(t)})`);
  }

  private parseArrayLiteral(): Operand {
    const values: Literal[] = [];
    if (this.peek()?.type === "op" && (this.peek() as { value: string }).value === "]") {
      this.advance();
      return { kind: "array", values };
    }
    while (true) {
      const t = this.advance();
      if (!t) throw new Error("condition-parser: unterminated array literal");
      if (t.type === "string") values.push(t.value);
      else if (t.type === "number") values.push(t.value);
      else if (t.type === "bool") values.push(t.value);
      else if (t.type === "null") values.push(null);
      else throw new Error(`condition-parser: array elements must be literals (got ${describe(t)})`);
      const next = this.peek();
      if (next?.type === "op" && next.value === ",") {
        this.advance();
        continue;
      }
      if (next?.type === "op" && next.value === "]") {
        this.advance();
        return { kind: "array", values };
      }
      throw new Error(`condition-parser: expected ',' or ']' (got ${describe(next)})`);
    }
  }

  private matchOp(op: string): boolean {
    const t = this.peek();
    if (t?.type === "op" && t.value === op) {
      this.advance();
      return true;
    }
    return false;
  }
}

function describe(t: Token | undefined): string {
  if (!t) return "<eof>";
  if (t.type === "op") return `op '${t.value}'`;
  if (t.type === "ident") return `ident '${t.value}'`;
  if (t.type === "string") return `string '${t.value}'`;
  if (t.type === "number") return `number ${t.value}`;
  if (t.type === "bool") return `bool ${t.value}`;
  return "null";
}

export function collectPaths(ast: ConditionAst): string[] {
  const out: string[] = [];
  const walk = (node: ConditionAst): void => {
    switch (node.kind) {
      case "and":
      case "or":
        walk(node.left);
        walk(node.right);
        return;
      case "not":
        walk(node.expr);
        return;
      case "compare":
        if (node.left.kind === "path") out.push(node.left.segments.join("."));
        if (node.right.kind === "path") out.push(node.right.segments.join("."));
        return;
    }
  };
  walk(ast);
  return out;
}

export function parseCondition(input: string): ConditionAst {
  const trimmed = input.trim();
  if (trimmed.length === 0) throw new Error("condition-parser: empty expression");
  const tokens = new Lexer(trimmed).tokenize();
  return new Parser(tokens).parseRoot();
}

export function evaluateCondition(ast: ConditionAst, context: Record<string, unknown>): boolean {
  switch (ast.kind) {
    case "and":
      return evaluateCondition(ast.left, context) && evaluateCondition(ast.right, context);
    case "or":
      return evaluateCondition(ast.left, context) || evaluateCondition(ast.right, context);
    case "not":
      return !evaluateCondition(ast.expr, context);
    case "compare":
      return evaluateCompare(ast, context);
  }
}

function evaluateCompare(
  node: Extract<ConditionAst, { kind: "compare" }>,
  context: Record<string, unknown>
): boolean {
  const left = resolveOperand(node.left, context);
  const right = resolveOperand(node.right, context);
  if (node.op === "==") return left === right;
  if (node.op === "!=") return left !== right;
  if (node.op === "in") {
    if (!Array.isArray(right)) return false;
    return right.includes(left as Literal);
  }
  return false;
}

function resolveOperand(op: Operand, context: Record<string, unknown>): unknown {
  if (op.kind === "literal") return op.value;
  if (op.kind === "array") return op.values;
  let cur: unknown = context;
  for (const seg of op.segments) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[seg];
  }
  return cur;
}
