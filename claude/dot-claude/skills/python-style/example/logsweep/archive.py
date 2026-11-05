import logging
import shutil
from pathlib import Path

from .errors import ArchiveError

log = logging.getLogger(__name__)


def archive_files(paths: list[Path], root: Path, archive_dir: Path) -> list[Path]:
    archived = []

    for path in paths:
        destination = archive_dir / path.relative_to(root)
        move_file(path, destination)
        archived.append(destination)

    return archived


def move_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(source, destination)

    except OSError as error:
        raise ArchiveError(f"could not move {source} to {destination}: {error}") from error

    log.debug("moved %s to %s", source, destination)
