import argparse
import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from logsweep.archive import archive_files
from logsweep.errors import ToolError
from logsweep.scan import find_stale_files
from logsweep.settings import Settings, load_settings

log = logging.getLogger("logsweep")


@dataclass(frozen=True, slots=True)
class Options:
    root: Path
    config_path: Path
    dry_run: bool
    verbose: bool


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_args(argv)
    configure_logging(options.verbose)

    try:
        settings = load_settings(options.config_path)
        stale_files = find_stale_files(options.root, settings)
        sweep(stale_files, options, settings)

    except ToolError as error:
        log.error("%s", error)
        return 1

    return 0


def parse_args(argv: Sequence[str] | None) -> Options:
    parser = argparse.ArgumentParser(prog="logsweep")
    parser.add_argument("root", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")

    namespace = parser.parse_args(argv)

    return Options(
        root=namespace.root,
        config_path=namespace.config,
        dry_run=namespace.dry_run,
        verbose=namespace.verbose,
    )


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, stream=sys.stderr, format="%(levelname)s %(message)s")


def sweep(stale_files: list[Path], options: Options, settings: Settings) -> None:
    if not stale_files:
        log.info("nothing to sweep")
        return

    if options.dry_run:
        print_plan(stale_files)
        return

    archive_dir = options.root / settings.archive_dir
    archived = archive_files(stale_files, options.root, archive_dir)

    print(f"archived {len(archived)} files to {archive_dir}")


def print_plan(stale_files: list[Path]) -> None:
    for path in stale_files:
        print(f"would archive {path}")


if __name__ == "__main__":
    raise SystemExit(main())
