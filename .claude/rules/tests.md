---
name: tests
description: Reglas al editar tests del meta-repo (generador, hooks, skills) y al diseñar test harness generado
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "hooks/tests/**"
  - "generator/**/__tests__/**"
  - "generator/renderers/tests.ts"
  - "templates/**/test*.hbs"
---

# Reglas — Tests

## Principio: test antes de implementación (hard-enforced)

Cuando la rama toca `generator/**` o `hooks/**`:

1. **Fase 1 de la rama = tests**. Commit 1 de código debe ser tests que FALLAN.
2. **Fase 2..N = implementación** que los hace pasar.
3. Hook `PreToolUse(Write)` verifica: para cada Write a `generator/lib/<x>.ts` o `hooks/<x>.py`, existe pair `generator/lib/__tests__/<x>.test.ts` / `hooks/tests/test_<x>.py` con última modificación anterior al Write.

Waiver: comentario `// test-waiver: <razón ≥20 chars>` al inicio del archivo. Hook valida longitud de la razón. Abuso detectado por `/pos:test-audit`.

## Pirámide

- **Unit** (mayoría): lógica pura, renderers individuales, validadores.
- **Integration** (medio): generador extremo a extremo en `tmp/`, hooks con subprocess real.
- **Selftest** (pocos, integrales): `bin/pos-selftest.sh` corre escenarios full: generar proyecto → correr sus hooks → crear rama fake → validar gates.

## Coverage

- Threshold meta-repo: 80% líneas, 75% branches.
- Declarado en `vitest.config.ts` y `pytest.ini`.
- Enforced por hook `pre-push.sh` + CI.
- Excluciones explícitas en `.testignore` (si fuese necesario) con razón.

## Patrones de test por tipo de artefacto

### Renderer del generador (`generator/renderers/*.ts`)

```ts
describe('render<X>', () => {
  it('produces stable output for profile:nextjs-app', async () => {
    const profile = loadFixture('nextjs-app');
    const files = render(profile);
    expect(files).toMatchSnapshot();
  });
  it('throws descriptive error on missing required field', () => {
    expect(() => render(invalidProfile)).toThrow(/profile\.testing\.unit\.framework/);
  });
});
```

### Hook Python

```python
def run_hook(payload: dict) -> dict:
    result = subprocess.run(
        ["python3", HOOK_PATH],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode in (0, 2)
    return json.loads(result.stdout) if result.stdout else {}

def test_denies_checkout_without_marker(tmp_path):
    payload = {"tool_input": {"command": "git checkout -b feat/x"}}
    out = run_hook(payload)
    assert out["permissionDecision"] == "deny"
```

### Skill

Smoke test parseo de frontmatter + (si tiene lógica) test end-to-end via `claude -p` con timeout.

## Generador emite test harness

Ver `generator/renderers/tests.ts`. Por stack detectado, emite:

| Stack | Unit | Integration | E2E | Coverage tool |
|---|---|---|---|---|
| Node (vitest) | `vitest` | `vitest --config vitest.integration.config.ts` | `playwright` | `c8` / `@vitest/coverage-v8` |
| Node (jest) | `jest` | `jest --selectProjects integration` | `playwright` | `jest --coverage` |
| Python | `pytest` | `pytest -m integration` | `pytest-bdd` | `pytest-cov` |
| Go | `go test` | `go test -tags=integration` | `ginkgo` | `go test -coverprofile` |
| Rust | `cargo test` | `cargo test --test '*'` | `cargo test --test e2e` | `cargo-tarpaulin` |

El harness emitido incluye: config files, `package.json` scripts / `Makefile` targets, ejemplo test de smoke, `.testignore`, guía rápida en `tests/README.md`.

## Prohibido

- Tests que dependen de orden de ejecución.
- Tests que leen red sin mock (excepto los marcados `@network`, que corren sólo en CI con secret).
- Tests con `sleep()` — usar esperas condicionales.
- Commentar tests que fallan para "arreglar después". Si no sirve, bórralo + justifica en kickoff.
