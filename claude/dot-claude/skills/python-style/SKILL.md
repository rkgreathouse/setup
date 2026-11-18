---
name: python-style
description: The user's Python house style for scripts and CLI tools (layout, entry module, spacing, typing, errors, tests). Use when writing, editing, scaffolding, or reviewing Python code.
---

# Python style

Every rule here is meant to be checked by a tool. `example/` is a complete project
written to these rules; `example/pyproject.toml` is the tool config to copy into a
new project. When a rule and the example seem to disagree, the example wins.

## Layout

Each tool is a package named after the tool, run with `python -m <tool>`. The repo
root holds three things: `pyproject.toml`, `config.yaml`, and the package. Lock
files, `.gitignore`, and `README.md` sit alongside without counting.

```
logsweep/
├── pyproject.toml
├── config.yaml
└── logsweep/
    ├── __init__.py
    ├── __main__.py      entry module
    ├── settings.py      config.yaml → frozen Settings
    ├── scan.py          support modules, one concern each
    ├── archive.py
    ├── errors.py
    └── tests/
        ├── __init__.py
        ├── test_main.py
        ├── test_scan.py
        └── ...
```

- Non-Python assets (templates, Dockerfiles) get their own top-level folders next
  to the package.
- Several tools in one repo: one package per tool, side by side, plus a `utils`
  package for shared code. Tools import `utils`; tools never import each other,
  so any tool can be lifted into its own repo. Distinct jobs become separate
  tools, each with its own parser, rather than argparse subcommands.

## Imports

- Inside a package, import relatively: `from .scan import find_stale_files`;
  tests reach up one level, `from ..scan import find_stale_files`.
- Across packages (a tool importing `utils`), and for stdlib and third-party
  code, import absolutely.

## Entry module (`__main__.py`)

The entry module is the only place that parses arguments, prints, and catches
errors. In order:

1. Imports, then `log = logging.getLogger("<tool>")`.
2. `Options`: a `@dataclass(frozen=True, slots=True)` holding every parsed flag.
3. `main(argv: Sequence[str] | None = None) -> int`, which reads as a list of
   steps: parse, set up logging, then one call per task inside a single
   `try`/`except ToolError`.
4. The step functions, in the order `main` calls them. `parse_args` builds the
   parser and converts the `Namespace` to `Options` immediately; the rest of the
   code receives `Options` and never sees a `Namespace`.
5. `if __name__ == "__main__": raise SystemExit(main())`.

## Functions

- One job per function, named verb-first (`find_stale_files`, `move_file`).
- Guard clauses: handle the failing case and return early; the main path stays
  unindented.
- Length is free; branching is capped. Cyclomatic complexity ≤ 10 (ruff `C901`)
  and nesting ≤ 4 blocks (ruff `PLR1702`). A long linear `main` is fine; a short
  function with tangled `if`s inside loops gets split.
- Plain functions over data. A class earns its place only when state genuinely
  lives on between calls.

## Comprehensions and the walrus

- Build a list, set or dict with a comprehension rather than a loop that only
  appends: `names = [user.name for user in users if user.is_admin]`.
- Keep it to one `for` and at most one `if`, with no comprehension inside another.
  Anything bigger is a loop, or a helper the comprehension calls:
  `[space_comments(block) for block in blocks]`.
- Use the walrus when a value is only needed to test it and act on it:

  ```python
  if (failure := find_failure(result)) is not None:
      return {root: [failure_finding(failure)]}
  ```

  A value used again later keeps its own assignment line, and a named condition
  (`is_own_line = ...` then `if is_comment and is_own_line:`) stays named.

## Spacing

A blank line separates each block from its neighbours:

- after the run of setup assignments, before the loop or condition that uses them;
- before and after every `if` / `for` / `while` / `with` / `try` block;
- between a `try` body and each `except` / `finally`;
- before a comment that introduces a condition, including when it opens a block.

An `if` body sits directly against its own `elif` / `else`.

`ruff format` deletes a blank line that opens a block. After running it, restore
the blank line before a comment that opens a block (see `example/logsweep/scan.py`).

## Types

- Annotate every parameter and every return type.
- Leave local variables unannotated, including empty containers: mypy infers
  `stale_files = []` from the later `stale_files.append(path)`.
- Records are frozen dataclasses with `slots=True`. Booleans read as questions
  (`is_admin`, `dry_run`).
- Untrusted input (parsed YAML, JSON) enters as `dict[str, object]` and is
  narrowed with `isinstance` into a dataclass in one function
  (`settings.parse_settings`).

## Constants and config

- Module level holds imports, a logger, dataclasses, functions, and at most two
  UPPER_CASE constants that are true facts (`SECONDS_PER_DAY`).
- Anything tunable, and any third constant, goes in `config.yaml`, loaded once
  into a frozen `Settings`.
- Two sources, each with its own job: flags choose how this run behaves
  (`--dry-run`, `--verbose`, `--config`); `config.yaml` holds the tunable values.
  Environment variables are left unread, so a run is fully described by its
  command line and its config file.
- State passes through parameters; module-level variables stay constant.

## Errors

- `errors.py` defines one `ToolError` base and a subclass per failure area
  (`ConfigError`, `ArchiveError`).
- Raise with the context needed to act: the path, the key, the value. Chain
  with `raise ... from error` when translating an `OSError` or similar.
- Only `main` catches, logs the message, and returns `1`.

## Output

- Results go to stdout through `print`, and only from the entry module.
- Diagnostics go to stderr through `logging`, configured once in `main` with
  `%(asctime)s %(levelname)s %(name)s: %(message)s` and
  `datefmt="%Y-%m-%d %H:%M:%S"`, giving
  `2026-11-05 14:02:11 ERROR logsweep.settings: config not found: nope.yaml`.
- The entry module logs as `logging.getLogger("<tool>")`; every other module
  uses `logging.getLogger(__name__)`.
- Exit codes: `0` success, `1` failure, `2` bad usage (argparse's own).

## Comments

Code carries its own meaning through names and small functions. Docstrings are
left out. A comment appears only above a condition whose reason is not visible
in the code, and states that reason in one line:

```python
# archived logs live under root too and would be swept again every run
if path.is_relative_to(archive_dir):
    continue
```

## Tests

- pytest, in `<tool>/tests/`, one `test_<module>.py` per module;
  `test_main.py` covers `__main__.py`.
- Test the entry module by calling `main([...])` and asserting the exit code and
  captured stdout.
- Test names state the behaviour: `test_skips_files_already_archived`.
- Use `tmp_path` for files; tests keep the same type-hint rules as the code.

## Files

A file stays under 400 lines, aiming for 350. Past that, split by concern.

## Finishing

The work is done when all four pass from the repo root:

```sh
uv run ruff format . && uv run ruff check --fix .   # then restore block-opening blank lines
uv run mypy .
uv run pytest
uv run python -m <tool> --help
```
