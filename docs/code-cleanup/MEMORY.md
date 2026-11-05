# code-cleanup: plan memory

Status: **parked.** The `python-style` skill (`claude/dot-claude/skills/python-style/`)
is being finished first, then used to write this CLI. Nothing here is built yet.

## Goal

One deterministic CLI that cleans and checks code against a single house style
across languages: same input, same result, locally and in CI.

## Decisions

| Topic | Decision |
|---|---|
| Name | `code-cleanup` (Python package `code_cleanup`) |
| Languages | Python first, then Java, TypeScript, Kotlin |
| Where | Its own new repo (not this one); not created yet |
| Implementation language | Python, written to the `python-style` skill, checked by itself |
| CI | Harness.io gate; fails the pipeline, never edits code |
| Local | Fixes formatting and safe lint issues before commit |
| Distribution | Central: projects reference one image + one Harness template |
| Style basis | The Python style is the reference; other languages translate it |

## CLI shape

```
code-cleanup fix                                # local: apply safe fixes
code-cleanup check                              # CI: report only, exit 1 on failure
code-cleanup check --language python java       # default: auto-detect
code-cleanup check --report junit > report.xml  # Harness Tests tab
```

## Architecture: three layers

1. **Core** (`code_cleanup`): CLI, rule engine, one `config.yaml` style spec,
   reporting (text, JSON, JUnit), language-neutral rules (layout, file length,
   constants threshold, tests mirror modules, tool packages never import each other).
2. **Structural rules written once over tree-sitter**: spacing fixer, complexity,
   nesting, module-constant count, entry-module shape. Each language plugin maps its
   node types onto the shared rule.
3. **Native tools wrapped, configured from the same spec**:
   - Python: ruff + mypy --strict + pytest
   - Java: google-java-format + Checkstyle/PMD/Error Prone + ArchUnit
   - TypeScript: Prettier + typescript-eslint + tsc + dependency-cruiser
   - Kotlin: ktfmt or ktlint + detekt

Repo layout follows the Python style (three root items plus one package per plugin):

```
code-cleanup/
├── pyproject.toml          uv workspace
├── config.yaml             the style spec
├── code_cleanup/           core
├── code_cleanup_python/
├── code_cleanup_java/
├── code_cleanup_typescript/
└── code_cleanup_kotlin/
```

Rule packs: a fixed core plus opt-in packs per project in `.style.yml`
(`python-cli` first; `python-api` and others later).

## Harness

- One container image with every tool pinned, so local and CI match.
- One step group template that reads `.style.yml`, runs `code-cleanup check`, and
  publishes JUnit to the Tests tab. Projects reference the template.
- Open: build infrastructure (Harness Cloud, self-hosted Kubernetes, or VMs) and
  which registry holds the image.

## Learned while designing the Python rules (ruff 0.17.3, mypy 2.4.1)

- `ruff format` always removes a blank line that opens a block, with no setting
  to keep it. Plan: `fix` runs `ruff format` then our spacer; `check` runs both
  on a copy and fails on any diff.
- `ruff format` keeps a blank line between `try` body and `except`.
- ruff has no file-length rule: the 350 warn / 400 fail cap is ours.
- `PLR1702` (nesting) is a preview rule: needs `preview = true` with
  `explicit-preview-rules = true`.
- mypy --strict infers `x = []` from a later `append`; pyright strict rejects
  it. That is why mypy was chosen.
- Ruff's formatter has few options (line length, quotes, indent, magic trailing
  comma); style beyond that is lint rules or our own checks.
- `add_subparsers` is a warning in our checker, not a failure: whether two jobs
  are distinct is a judgement call.
- Relative imports inside a package are the house rule, but ruff can only ban
  them (`TID252`), never require them. The example turns `TID252` off; requiring
  relative imports within a package is a custom check for code-cleanup.
- Python 3.14 is the latest stable release (3.15 still in beta as of 2026-11).

## Order of work

1. ~~Finish the `python-style` skill.~~ Done (line length 88).
2. Create the `code-cleanup` repo; build core + Python plugin + Harness template
   using the skill.
3. Java, TypeScript, Kotlin plugins, modelled on the Python one.
