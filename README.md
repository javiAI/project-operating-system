# project-operating-system (`pos`)

Meta-repo que genera y opera proyectos con Claude Code de forma determinista, token-eficiente y libre de ambigüedad.

- **Qué hace**: cuestionario → `project_profile.yaml` → genera un repo con CLAUDE.md + skills + hooks + policy + CI/CD + test harness adaptado al stack.
- **Cómo se distribuye**: plugin Claude Code (`pos`). Instalable local (`--plugin-dir`) o vía marketplace público (repo `javiAI/pos-marketplace`).
- **Fuente de verdad ejecutable**: [MASTER_PLAN.md](MASTER_PLAN.md).
- **Estado vivo**: [ROADMAP.md](ROADMAP.md).
- **Quickref sesión**: [HANDOFF.md](HANDOFF.md).
- **Arquitectura canónica**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Política de seguridad comunidad**: [docs/SAFETY_POLICY.md](docs/SAFETY_POLICY.md).

## Antes de tocar nada

Lee [CLAUDE.md](CLAUDE.md) y [AGENTS.md](AGENTS.md). El flujo de ramas tiene Fase -1 (aprobación explícita) que es hard-gate por hook.

## Licencia

MIT.
