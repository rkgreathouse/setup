# code-cleanup: plan memory

Status: **v0.1 built: core + Python plugin**, in `rkgreathouse/code-cleanup`,
written to the `python-style` skill (`claude/dot-claude/skills/python-style/`) and
checked by itself, on branch `claude/code-cleanup-cli-s4flvc`. The first push was
refused (Claude GitHub App not yet installed on that repo). Not yet published to
PyPI; no Harness template yet.

## Goal

One deterministic CLI that cleans and checks code against a single house style
across languages: same input, same result, locally and in CI.

## Decisions

| Topic | Decision |
|---|---|
| Name | `code-cleanup` (Python package `code_cleanup`) |
| Languages | Python first, then Java, TypeScript, Kotlin |
| Where | `rkgreathouse/code-cleanup` |
| Distribution | PyPI package `code-cleanup` (name was free on 2026-11-05); `pip install code-cleanup` |
| Implementation language | Python, written to the `python-style` skill, checked by itself |
| CI | Harness.io gate; fails the pipeline, never edits code |
| Local | Fixes formatting and safe lint issues before commit |
| CI distribution | Central: projects reference one image + one Harness template |
| Style basis | The Python style is the reference; other languages translate it |

## CLI shape (as built)

```
code-cleanup [ROOT]                              # local: fix in place (ROOT defaults to .)
code-cleanup --check                             # CI: report only, exit 1 on diff or error
code-cleanup --check --report junit > report.xml # Harness Tests tab (also text, json)
code-cleanup --config FILE                       # default ROOT/.code-cleanup.yaml
```

- **No `--language` flag.** `router.py` maps each file to a plugin by suffix or
  exact file name (`.gitignore`);
  files no plugin claims are skipped. Discovery uses `git ls-files` (so `.gitignore`
  holds) and falls back to walking the tree outside a work tree; `exclude` folder
  names apply either way.
- **No subcommands.** The skill says distinct jobs are separate tools; fix and check
  are one job with a flag choosing how the run behaves (like `--dry-run`).

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

Repo layout as built: one distribution, one package, one subpackage per language
(simpler to publish than the uv workspace first planned):

```
code-cleanup/
├── pyproject.toml          hatchling; console script code-cleanup
└── code_cleanup/
    ├── __main__.py         entry module (skill shape)
    ├── settings.py         style.yaml + project .code-cleanup.yaml → frozen Settings
    ├── style.yaml          the house style spec, shipped in the wheel
    ├── discover.py         git ls-files / walk, minus exclude
    ├── router.py           suffix/name → Language(clean, check_project)
    ├── engine.py           clean each file, then each language's project pass
    ├── report.py           text / json / junit, exit decision
    ├── tools.py            pinned binary lookup (venv scripts dir, then PATH)
    ├── python/             ruff, spacing, imports, checks, logs, mypy, layout, clean
    ├── toml/               taplo, spacing, clean
    ├── ignore/             clean (.gitignore, .dockerignore)
    └── tests/              test_<module>.py, test_<subpackage>_<module>.py
```

- **The flow** (decided with the user): ruff (fix, format) → our fixes (spacing,
  relative imports) → checks: ruff lint, then mypy --strict, then our `CC` rules.
  A plugin has a per-file `clean` and an optional whole-project `check_project`.
- **mypy** is a pinned runtime dependency, run once per root on a temp copy of the
  cleaned files (line numbers match, no cache in the project), using ROOT/.venv for
  third-party packages. Exit 2, or exit 1 with no JSON report (mypy missing), is one
  `mypy` finding: a clean install once passed silently without it.
- **Profiles**: `profile: none` (default, file rules only) or `cli` (python-style
  layout, `CC3xx`). `service` is planned with Java: JSON logs, REST layout. The
  logging format is a setting so a profile can swap it.
- **Logging is checked, not shipped as a package.** Python setup is ten lines of
  stdlib in `main`; a runtime library would add a dependency to every tool. Shared
  logging *config* (log4j2.xml, Spring logging properties) belongs to the planned
  templates layer, with code-cleanup reporting drift.
- **TOML**: taplo 0.9.3 (`--no-auto-config`, options from style.yaml), chosen over
  tombi, which reorders keys by schemastore schemas and warned on unresolved refs.
  Our pass adds a blank line above each `[table]` and its comments.
- **Ignore files**: sort within a block and drop repeats only where no `!` negation
  makes order matter, so the ignored set never changes.

- The style ships inside the package, not as a root `config.yaml` (a deviation from
  the skill's layout): a published tool's defaults must be in the wheel, and
  `config.yaml` in a target repo is that project's own config. Projects override
  keys in `.code-cleanup.yaml` (mappings merge, lists replace); that replaces the
  `.style.yml` rule-pack idea for now.
- Custom rules (e.g. the blank line above a comment that opens an `if`) are
  switches under `python.spacing` / `python.checks` in the style.
- Codes are grouped by concept so Java maps onto the same numbers: `CC0xx` file
  (`CC000` syntax, `CC001` length), `CC1xx` modules (`CC101` absolute self-import,
  auto-fixed for `from` imports; `CC102` third+ constant; `CC103` docstring;
  `CC104` environment read; `CC105` comprehension with more than one for/if or
  nested; `CC106` walrus suggestion, a warning, only for x / not x / x is None
  tests of a value used nowhere else), `CC2xx` logging (`CC201` basicConfig outside entry,
  `CC202` logger name, `CC203` format), `CC3xx` layout under `profile: cli`
  (`CC301` root module, `CC302` untested module, `CC303` entry shape, `CC304`
  errors.py, `CC305` tool imports tool), `CC4xx` config files (`CC401` ignore
  block without header). Plus `mypy:<code>` and ruff codes.

## Harness

- One container image with every tool pinned, so local and CI match.
- One step group template that reads `.style.yml`, runs `code-cleanup check`, and
  publishes JUnit to the Tests tab. Projects reference the template.
- Open: build infrastructure (Harness Cloud, self-hosted Kubernetes, or VMs) and
  which registry holds the image.

## Learned while building v0.1

- ruff `--config "key = value"` overrides are applied in an order that can drop
  `lint.ignore` when `lint.select` is also passed. Instead the style is rendered to
  a `ruff.toml` (named by content hash, in the temp dir) and passed as
  `--config FILE`, which also disables discovery of the project's ruff config.
  `**/__main__.py` per-file-ignores still match files anywhere.
- Pipeline per Python file, all via stdin: `ruff check --fix --exit-zero` →
  `ruff format` → spacing pass → `ruff check --output-format json`. Running the
  spacing pass last makes the whole pipeline idempotent (tested).
- Calling the ruff binary from the venv scripts dir instead of `python -m ruff`
  made a run 4x faster (~20 ms per file).
- ruff 0.17's `--fix` applies PTH fixes such as `os.remove` → `Path.unlink`.
- The spacing pass inserts/removes only blank lines at statement and clause
  starts, found with `ast` + `tokenize` (so lines inside strings are never touched).

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
2. ~~Core + Python plugin.~~ Done (v0.1.0).
3. ~~Python round two~~: mypy in the flow, profiles + layout, logging rules, env
   check, CC101 auto-fix, TOML and ignore-file plugins. Done.
4. Publish to PyPI (trusted publishing from a release workflow), container image,
   Harness step group template; file-list arguments for pre-commit; parallel runs.
5. Java, TypeScript, Kotlin plugins, modelled on the Python one; each takes its
   spacing and decomposition rules from the Python style.
6. Non-code files: Spring `application.yml`/`.properties`, log4j2 config; then project-structure rules (e.g. REST API
   layout) for a broader "one style" skill that also writes the CI check.
