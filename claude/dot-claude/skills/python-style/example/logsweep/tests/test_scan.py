import os
import time
from pathlib import Path

from ..scan import find_stale_files
from ..settings import Settings


def make_settings() -> Settings:
    return Settings(max_age_days=30, archive_dir="archive", patterns=("*.log",))


def write_log(path: Path, age_days: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("entry\n")

    modified = time.time() - age_days * 86_400
    os.utime(path, (modified, modified))

    return path


def test_finds_only_files_older_than_max_age(tmp_path: Path) -> None:
    old_log = write_log(tmp_path / "old.log", age_days=40)
    write_log(tmp_path / "new.log", age_days=1)

    assert find_stale_files(tmp_path, make_settings()) == [old_log]


def test_skips_directories_named_like_logs(tmp_path: Path) -> None:
    (tmp_path / "app.log").mkdir()

    assert find_stale_files(tmp_path, make_settings()) == []


def test_skips_files_already_archived(tmp_path: Path) -> None:
    write_log(tmp_path / "archive" / "old.log", age_days=40)

    assert find_stale_files(tmp_path, make_settings()) == []
