import time
from pathlib import Path

from .settings import Settings

SECONDS_PER_DAY = 86_400


def find_stale_files(root: Path, settings: Settings) -> list[Path]:
    cutoff = time.time() - settings.max_age_days * SECONDS_PER_DAY
    archive_dir = root / settings.archive_dir
    stale_files = []

    for pattern in settings.patterns:
        for path in root.rglob(pattern):

            # rglob also matches directories named like "app.log"; only files are swept
            if not path.is_file():
                continue

            # archived logs live under root too and would be swept again every run
            if path.is_relative_to(archive_dir):
                continue

            if is_older_than(path, cutoff):
                stale_files.append(path)

    return sorted(stale_files)


def is_older_than(path: Path, cutoff: float) -> bool:
    return path.stat().st_mtime < cutoff
